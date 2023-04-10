import logging
import logging.handlers
import os
import argparse
import json
import requests
from bs4 import BeautifulSoup, NavigableString, Tag

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger_file_handler = logging.handlers.RotatingFileHandler(
    "status.log",
    maxBytes=1024 * 1024,
    backupCount=1,
    encoding="utf8",
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger_file_handler.setFormatter(formatter)
logger.addHandler(logger_file_handler)

# try:
#     SERVICE_ACC = os.environ["SERVICE_ACC"]
# except KeyError:
#     SERVICE_ACC = "Token not available!"
#     logger.info("Token not available!")
#     raise

def setup_file(filename,is_append):
    if is_append:
        mod = "a+"
        bra = ']'
    else :
        mod = "w"
        bra = '['
    with open(filename, mod) as f:
        f.writelines(bra)

def write_file(filename, data, deli):
    with open(filename,"a+") as f:
        f.writelines(deli)
        json.dump(data,f,indent=2,ensure_ascii=False)

def add_contents(contents,data):
    for header in contents.find_all("h3"):
        nextNode = header
        while True:
            nextNode = nextNode.nextSibling
            if nextNode is None:
                break
            if isinstance(nextNode, NavigableString):
                # print (nextNode.strip())
                pass
            if isinstance(nextNode, Tag):
                if nextNode.name == "h3":
                    break
                # print (nextNode.get_text(strip=True).strip())
                data[header.text]=nextNode.get_text(strip=True).strip()

def get_list_link(start, end):  
    links = []
    for i in range(start,end+1):
        links.append(f"https://www.topcv.vn/tim-viec-lam-lap-trinh-vien?salary=0&exp=0&sort=up_top&page={i}")
    return links

def get_titles(list_link):
    titles = []
    for link in list_link :
        response = requests.get(link)
        soup = BeautifulSoup(response.content, "html.parser")
        title = soup.findAll('h3', class_='title')
        for tit in title:
            titles.append(tit)
    return titles
# links_company = [link_company.find('a').attrs["href"] for link_company in titles]

def get_links_company(titles): 
    links_company =[]
    for link_company in titles:
        link_obj = link_company.find("a")
        if link_obj != None:
            link = link_obj["href"]
            links_company.append(link)
    return links_company
    

def crawl_contents(filename,links_company):
    setup_file(filename,False)
    deli = ""

    for link in links_company:

        news = requests.get(link)
        soup = BeautifulSoup(news.content, "html.parser")
        names_obj = soup.find('a', class_="company-logo")
        if names_obj == None :
            continue
        names = names_obj.attrs["title"]  
        data= {} 
        data["job_url"] = str(link)
        data["company_name"]=names

        job_obj = soup.find("h1", class_="job-title text-highlight bold")
        job_title = job_obj.find("a")
        salary = soup.select("#tab-info > div > div > div.col-md-8 > div.box-info > div > div:nth-child(1) > div > span")
        exp = soup.select("#tab-info > div > div > div.col-md-8 > div.box-info > div > div:nth-child(6) > div > span")
        location = soup.select("#tab-info > div > div > div.col-md-4.col-box-right > div.box-keyword-job > div.area > span:nth-child(1) > a")
        if job_title == None or salary == [] or exp == [] or location == []:
            continue
        data["job_title"] = job_title.text
        data["salary"] = salary[0].text.strip()
        data["exp"] = exp[0].text
        data["location"] = location[0].text

        contents= soup.find("div", class_="job-data")
    
        add_contents(contents,data)

        write_file(filename, data, deli)
        deli = ",\n"
    setup_file(filename,True)

if __name__=="__main__":
    import os  
    import datetime 

    # create parser
    logger.info("Parsing Args")
    parser = argparse.ArgumentParser()
    parser.add_argument("start")
    parser.add_argument("end")
    args = parser.parse_args()
 
    logger.info(f"Start crawling from {args.start} to {args.end}")
    # data = read_data(args.data_file_name)
    links = get_list_link(int(args.start),int(args.end))
    logger.info("list of links")
    logger.info(links)
    title = get_titles(links)
    links_company = get_links_company(title)

    now = datetime.datetime.now()
    date_time = now.strftime("%Y/%m/%d")
    src_path = os.getcwd() + "/raw_data"
    if not os.path.exists(src_path):
        os.makedirs(src_path)
    if not os.path.exists(f"{src_path}/{date_time}"):
        os.makedirs(f"{src_path}/{date_time}")

    filename = "recruit_"+args.start+"_"+args.end+".json"
    crawl_contents(f"{src_path}/{date_time}/{filename}", links_company)