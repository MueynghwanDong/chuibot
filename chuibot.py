import re
import urllib.request

from bs4 import BeautifulSoup

from flask import Flask
from slack import WebClient
from slackeventsapi import SlackEventAdapter

app = Flask(__name__)
# /listening 으로 슬랙 이벤트를 받습니다.
slack_events_adaptor = SlackEventAdapter(SLACK_SIGNING_SECRET, "/listening", app)
slack_web_client = WebClient(token=SLACK_TOKEN)


# 크롤링 함수 구현하기
def _crawl(text):
    # 여기에 함수를 구현해봅시다.
    if "마감" in text:
        url = "http://www.saramin.co.kr/zf_user/calendar?cal_cd=1&cal_dt=2019-07&scrap=&keyword=&cal_kind%5B%5D=end&pr_exp_lv%5B%5D=1&pr_exp_lv%5B%5D=0&up_cd%5B%5D=3&up_cd%5B%5D=4&up_cd%5B%5D=9#listTop"
        req = urllib.request.Request(url)

        sourcecode = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(sourcecode, "html.parser")

        today = soup.find("td", class_="today").find("span", class_="date").get_text()

        companies = []
        employ_infos = []
        end_dates = []
        messages = []
        links = []
        salary_links = []
        salaries = []

        for i in range(3):
            for j, info in enumerate(
                soup.find("div", class_="public_recruit_layer_container layer_" + str(int(today) + i)).find_all("tr")):
                companies.append(info.find("td", class_="company").find("span").get_text())
                employ_infos.append(info.find("a").find("span").get_text())
                # end_dates.append(info.select("td")[3].get_text())
                links.append("http://saramin.co.kr" + info.find("a")["href"])

        for k in range(len(links)):
            url = links[k]
            source_code = urllib.request.urlopen(url).read()
            soup = BeautifulSoup(source_code, "html.parser")
            end_dates.append(soup.find("dl", class_="info_period").select("dd")[1].get_text())
            if soup.find("a", title="연봉정보 이동"):
                salary_links.append("http://saramin.co.kr" + soup.find("a", title="연봉정보 이동")["href"])
            else:
                salary_links.append("연봉정보 X")

        for l in range(len(salary_links)):
            if salary_links[l] == "연봉정보 X":
                salaries.append("연봉정보 X")
            else:
                url = salary_links[l]
                source_code = urllib.request.urlopen(url).read()
                soup = BeautifulSoup(source_code, "html.parser")
                salaries.append(soup.find("div", class_="list_range").select("dd")[2].get_text()+"만원")

        messages.append("회사" + ' / ' + "공고명" + ' / ' + "마감일" + ' / ' +"대졸 사원 평균 연봉")
        for m, company in enumerate(companies):
            messages.append(str(m + 1) + ".  "+companies[m] + ' / ' + employ_infos[m] + ' / ' + end_dates[m] + ' / ' + salaries[m])
            messages.append(links[m])

        return u'\n'.join(messages)

    elif "시작" in text:
        list_href = []
        list_content = []
        url = "http://www.saramin.co.kr/zf_user/calendar?cal_cd=1&cal_dt=2019-07&scrap=&keyword=&cal_kind%5B%5D=start&pr_exp_lv%5B%5D=1&up_cd%5B%5D=3&up_cd%5B%5D=4&up_cd%5B%5D=9#listTop"
        req = urllib.request.Request(url)
        sourcecode = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(sourcecode, "html.parser")
        days = []
        list_href = []
        gonggo = []
        company = []
        todaydate = soup.find("td", class_="today").find("span", class_="date").get_text()
        print(todaydate)
        for i in range(3):
            days.append(int(todaydate) - i)

        for i in range(3):
            for info in soup.find("div",
                                  class_="public_recruit_layer_container layer_" + str(int(todaydate) - i)).find_all(
                    "td", class_="company"):
                company.append(info.find("span").getText())
        for i in range(3):
            for info in soup.find("div",
                                  class_="public_recruit_layer_container layer_" + str(int(todaydate) - i)).find_all(
                    "td", class_="title"):
                list_href.append(info.find("a")["href"])
                gonggo.append(info.find("span").getText())

        idxs = []
        print(len(list_href))
        for i in range(0, len(list_href)):
            idxs.append(list_href[i][32:48])
        # print(idxs)
        newhref = []

        startcontent = []
        endcontent = []
        salarydata = []
        salarymoney = []
        for i in range(0, len(idxs)):
            newhref.append("http://www.saramin.co.kr/zf_user/jobs/relay/pop-view?t_ref=calendar&" + idxs[
                i] + "&view_type=public-recruit")
            # print(newhref)
            url = newhref[i]
            source_code = urllib.request.urlopen(url).read()
            soup = BeautifulSoup(source_code, "html.parser")
            startcontent.append(soup.find("dl", class_="info_period").select("dd")[0].getText().strip())
            endcontent.append(soup.find("dl", class_="info_period").select("dd")[1].getText().strip())
            if soup.find("a", title="연봉정보 이동"):
                salarydata.append("http://www.saramin.co.kr" + soup.find("a", title="연봉정보 이동")["href"])
            else:
                salarydata.append("등록되지 않음")
        for i in range(0, len(salarydata)):
            if (salarydata[i] != "등록되지 않음"):
                url = salarydata[i]
                source_code = urllib.request.urlopen(url).read()
                soup = BeautifulSoup(source_code, "html.parser")
                salarymoney.append(soup.find("div", class_="list_range").select("dd")[2].getText().strip()+"만원")
            else:
                salarymoney.append("등록 안됨")

        totalmessage = []
        totalmessage.append("회사" + ' / ' + "공고명" + ' / ' + "마감일" + ' / ' + "대졸 사원 평균 연봉")
        for i in range(0, len(company)):
            totalmessage.append(str(i + 1) + ".  " + company[i] + " / " + gonggo[i] + " / " + "시작 일 : " + startcontent[
                i] + " / " + "마감 일 : " + endcontent[i] + " / " + salarymoney[i] )
            totalmessage.append(newhref[i])

        return u'\n'.join(totalmessage)

    elif "순위" in text:
        rankings = []
        companies = []
        ratings = []
        headers = {'User-Agent': 'Chrome/66.0.3359.181'}
        messages = []

        for i in range(1, 3):
            url = "https://www.jobplanet.co.kr/companies?sort_by=review_avg_cache&industry_id=700&page=" + str(i)
            req = urllib.request.Request(url, headers=headers)
            sourcecode = urllib.request.urlopen(req).read()
            soup = BeautifulSoup(sourcecode, "html.parser")

            for j, data in enumerate(soup.find_all("div", class_="ty3_wrap")):
                rankings.append(data.find("li", class_="content_col2_1").find("span").get_text())
                companies.append(data.find("dt", class_="us_titb_l3").find("a").get_text())
                ratings.append(data.find("span", class_="gfvalue").get_text())

        for k in range(20):
            messages.append(rankings[k] + '/' + companies[k] + '/' + ratings[k])

        return u'\n'.join(messages)

    elif "" in text:
        return "저를 사용하는 명령어는 시작, 마감, 순위 입니다"

    else:
        return "다시 입력해주세요"



# 챗봇이 멘션을 받았을 경우
@slack_events_adaptor.on("app_mention")
def app_mentioned(event_data):
    channel = event_data["event"]["channel"]
    text = event_data["event"]["text"]
    message = _crawl(text)
    slack_web_client.chat_postMessage(
        channel=channel,
        text=message
    )



    # / 로 접속하면 서버가 준비되었다고 알려줍니다.
@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"

if __name__ == '__main__':
    app.run('127.0.0.1', port=4040, threaded=True)
