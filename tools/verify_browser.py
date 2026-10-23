"""Optional real-browser UI checks. Requires Playwright; no Gemini key is used.

python -m pip install playwright
python -m playwright install chromium
python tools/verify_browser.py --start-server
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import urlopen
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
INIT_OBSERVER = '''() => {
  window.__loadingSamples = [];
  let start = null;
  new MutationObserver(() => {
    const visible = document.querySelector('.answer-loading');
    if (visible && start === null) start = performance.now();
    if (!visible && start !== null) {
      window.__loadingSamples.push(performance.now() - start);
      start = null;
    }
  }).observe(document, {childList:true, subtree:true});
}'''


def run_checks(url, executable, output):
    output.mkdir(parents=True, exist_ok=True)
    reports = []
    with sync_playwright() as p:
        for name, width, height in [('desktop',1280,800), ('mobile',390,844)]:
            options = dict(headless=True)
            if executable:
                options.update(executable_path=executable, args=['--no-sandbox','--disable-dev-shm-usage','--no-zygote','--single-process','--in-process-gpu','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
            browser = p.chromium.launch(**options)
            context = browser.new_context(viewport={'width':width,'height':height}, is_mobile=name=='mobile', has_touch=name=='mobile')
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.add_init_script('('+INIT_OBSERVER+')()')
            try:
                page.goto(url)
                box = page.get_by_placeholder('Ask FAST a question…')
                box.wait_for(timeout=30000)
                assert box.bounding_box()['y'] > height / 2, 'Composer is not at bottom'
                checks = []
                def ask(question, expected, sequence):
                    box.fill(question)
                    box.press('Enter')
                    page.locator('.answer-loading').wait_for(state='visible', timeout=10000)
                    assert box.is_disabled(), 'Composer enabled during pending turn'
                    if sequence == 1:
                        page.screenshot(path=str(output/f'{name}-loading.png'))
                    page.wait_for_function("expected => {const all=document.querySelectorAll('[data-testid=stChatMessage]'); const last=all[all.length-1]; return last && last.innerText.includes(expected) && !document.querySelector('.answer-loading');}", arg=expected, timeout=30000)
                    page.wait_for_function("key => window.__fastScrollEvent === key", arg=f'{sequence}-complete', timeout=10000)
                    page.wait_for_timeout(900)
                    assert not box.is_disabled(), 'Composer stayed disabled after reply'
                    metrics = page.evaluate("""() => {
                      const main=document.querySelector('.stMain');
                      return {gap:main.scrollHeight-main.scrollTop-main.clientHeight, scrollTop:main.scrollTop,
                        overflow:document.documentElement.scrollWidth-innerWidth,
                        replyBottom:Array.from(document.querySelectorAll('[data-testid=stChatMessage]')).at(-1).getBoundingClientRect().bottom,
                        composerTop:document.querySelector('[data-testid=stChatInput]').getBoundingClientRect().top};
                    }""")
                    assert metrics['gap'] < 180, f'Latest reply not reached: {metrics}'
                    assert metrics['overflow'] <= 1, f'Horizontal page overflow: {metrics}'
                    assert 0 < metrics['replyBottom'] <= metrics['composerTop'] + 8, f'Reply hidden by composer: {metrics}'
                    checks.append({'question':question,'scroll_gap_px':round(metrics['gap']), 'passed':True})
                ask('TELL ME ABOUT FACULTY', 'kundusukanta@yahoo.com', 1)
                text = page.locator('[data-testid=stChatMessage]').last.inner_text()
                assert text.index('Dileep') < text.index('Vandana') < text.index('Ravi'), 'Faculty order changed'
                main = page.locator('.stMain')
                before = main.evaluate('(e) => e.scrollTop')
                if name == 'desktop':
                    page.mouse.move(width/2, height/2)
                    page.mouse.wheel(0,-400)
                else:
                    # A touchmove event cancels following; programmatic scroll simulates drag.
                    page.evaluate("document.dispatchEvent(new Event('touchmove',{bubbles:true})); document.querySelector('.stMain').scrollTop=0")
                page.wait_for_timeout(300)
                assert main.evaluate('(e) => e.scrollTop') < before, 'Manual scroll up was blocked'
                ask('MCA fees', '100,000', 2)
                ask('xyzabc', 'Could you rephrase', 3)
                assert page.get_by_role('link', name='Open student ERP').get_attribute('href') == 'https://erp.jlu.edu.in/Login.aspx'
                page.get_by_role('button', name='Faculty', exact=True).click()
                page.wait_for_function("() => window.__fastScrollEvent === '4-complete'", timeout=30000)
                page.wait_for_timeout(900)
                assert 'kundusukanta@yahoo.com' in page.locator('[data-testid=stChatMessage]').last.inner_text()
                samples = page.evaluate('window.__loadingSamples')
                assert len(samples) >= 4, f'Loader missing on a turn: {samples}'
                assert min(samples) >= 200, f'Loader disappeared too quickly: {samples}'
                page.screenshot(path=str(output/f'{name}.png'))
                assert not errors, f'Browser JavaScript errors: {errors}'
                reports.append({'viewport':name,'width':width,'height':height,'checks':checks,
                                'loader_samples_ms':[round(n) for n in samples], 'topic_button_passed':True,
                                'manual_scroll_passed':True,'javascript_errors':errors})
            except Exception:
                page.screenshot(path=str(output/f'{name}-failure.png'))
                print(json.dumps({'viewport':name, 'scroll_nodes':page.evaluate("() => Array.from(document.querySelectorAll('*')).filter(e=>e.scrollHeight>e.clientHeight+100 && e.clientHeight>100).map(e=>({tag:e.tagName,testid:e.dataset.testid,classes:e.className,overflow:getComputedStyle(e).overflowY,top:e.scrollTop,height:e.clientHeight,total:e.scrollHeight}))"), 'body':page.locator('body').inner_text()[-500:]},ensure_ascii=False))
                raise
            finally:
                browser.close()
    return reports


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--start-server',action='store_true')
    parser.add_argument('--base-url',default='http://127.0.0.1:8517/')
    parser.add_argument('--browser-executable')
    parser.add_argument('--output',default='/tmp/fast-browser-check')
    args=parser.parse_args()
    server=None
    try:
        if args.start_server:
            server=subprocess.Popen([sys.executable,'-m','streamlit','run','app.py','--server.port=8517','--server.address=127.0.0.1','--server.headless=true'], cwd=ROOT,
                                    env={**os.environ,'GEMINI_API_KEY':'','SHOW_API_SETTINGS':'false','JLU_ERP_URL':'https://erp.jlu.edu.in/Login.aspx'},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            for _ in range(100):
                try:
                    urlopen(args.base_url+'_stcore/health',timeout=1)
                    break
                except Exception:
                    time.sleep(.2)
            else:
                raise RuntimeError('Local test server did not start')
        report=run_checks(args.base_url,args.browser_executable,Path(args.output))
        Path(args.output,'browser_report.json').write_text(json.dumps(report,indent=2))
        print(json.dumps(report,indent=2))
    finally:
        if server:
            server.terminate()
            server.wait(timeout=10)

if __name__=='__main__':
    main()
