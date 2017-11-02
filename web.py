import webbrowser
import multiprocessing

def openBrowser(url):
    webbrowser.open_new(url)
    
def startBrowserInSeperateProcess(url):
    process = multiprocessing.Process(target=openBrowser,args=(url, ))
    process.start()
    return process
    
    
    
