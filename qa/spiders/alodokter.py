import scrapy
import w3lib.html
from bs4 import BeautifulSoup
import csv

class Alodokter(scrapy.Spider):
  name = "alodokter"
  start_urls = []
  current_page = 1

  def start_requests(self):
    with open('alodokter_links.csv', newline='') as f:
      reader = csv.reader(f)
      for row in reader:
        self.start_urls.append(row[1])

    yield scrapy.Request(self.start_urls.pop(), callback=self.parse)

  def parse(self, response):
    print('http status', response.status)
    if (response.status == 404):
      yield scrapy.Request(self.start_urls.pop(), callback=self.parse)
      self.current_page = 1

    else:
      topics = response.css('card-topic')
      if (len(topics) != 0):
        self.current_page += 1
        url = response.request.url+'/page/'+str(self.current_page)

        for topic in topics:
          href = 'https://alodokter.com'+topic.css('card-topic::attr(href)').get()
          yield scrapy.Request(href, callback=self.parse_content)

        if (self.current_page > 2):
          url = response.request.url.rsplit('/', 1)[0]+'/'+str(self.current_page)

        print(response.request.url)
        yield scrapy.Request(url, callback=self.parse)


  def clean_txt(self, txt):
    t = txt.replace('\\n','').replace("\\u003c","<").replace("\\u003e",">").replace("\"","").replace("\\t"," ").replace("\\r"," ").replace("\xa0"," ")
    return BeautifulSoup(t, "lxml").get_text(separator=' ')

  def parse_content(self, response):
    question = response.css('detail-topic::attr(member-topic-content)').get()
    question = self.clean_txt(question)
    answer = response.css('doctor-topic[doctor-title-small=Dokter]::attr(doctor-topic-content)').get()
    answer = self.clean_txt(answer)

    replies = response.css('doctor-topic')
    replies_data = []
    for reply in replies:
      comment = reply.css('doctor-topic::attr(doctor-topic-content)').get()
      comment = self.clean_txt(comment)
      replies_data.append({
        'user': reply.css('doctor-topic::attr(doctor-name-title)').get(),
        'utype': reply.css('doctor-topic::attr(doctor-title-small)').get(),
        'comment': comment,
        'comment_at': reply.css('doctor-topic::attr(post-date)').get(),
      })
    
    yield {
      'user': response.css('detail-topic::attr(member-username)').get(),
      'title': response.css('detail-topic::attr(member-topic-title)').get(),
      'question': question,
      'question_date': response.css('detail-topic::attr(member-post-date)').get(),
      'answer': answer,
      'answer_date': response.css('doctor-topic[doctor-title-small=Dokter]::attr(post-date)').get(),
      'doctor': response.css('doctor-topic[doctor-title-small=Dokter]::attr(doctor-name-title)').get(),
      'replies': replies_data,
      'url': response.request.url
    }
