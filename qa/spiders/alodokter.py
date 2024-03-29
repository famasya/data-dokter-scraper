import scrapy
import w3lib.html
from bs4 import BeautifulSoup
import csv
import urllib

class Alodokter(scrapy.Spider):
  name = "alodokter"
  start_urls = []
  topic_url = ""
  current_page = 1

  def start_requests(self):
    remote_file = getattr(self,'remote_file','')
    if(remote_file != ''):
      print('Remote mode')
      csv_url = "https://raw.githubusercontent.com/famasya/data-dokter-scraper/main/alodokter_links.csv?token=AC53AHDADFTTSWSVZQEMZ4DACVBGG"
      response = urllib.request.urlopen(csv_url)
      lines = [l.decode('utf-8') for l in response.readlines()]
      reader = csv.reader(lines)
      for row in reader:
        self.start_urls.append(row[1])
    else:
      print('Local mode')
      with open('alodokter_links.csv', newline='') as f:
        reader = csv.reader(f)
        for row in reader:
          self.start_urls.append(row[1])
    
    self.start_urls.pop(0)
    self.topic_url = self.start_urls.pop()
    yield scrapy.Request(self.topic_url, callback=self.parse)

  def parse(self, response):
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

      is_next = response.css('paginate-button::attr(next-page)').get()
      if(is_next != '0'):
        yield scrapy.Request(url, callback=self.parse)
      else:
        print('page done')
        self.current_page = 1
        self.topic_url = self.start_urls.pop()
        yield scrapy.Request(self.topic_url, callback=self.parse)


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
      'url': response.request.url,
      'topic_url': self.topic_url
    }
