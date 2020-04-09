# 专利页面爬虫(请酌情爬取)
>注：本项目为v2，第一版参见：[CrawlPage](https://github.com/sky94520/CrawlPage)<br>
>该版本目前最多能爬取的专利是6000条，v1可以完全爬取，但代码方面难以维护。
>针对知网专利，本代码由两部分组成:<br>
>第一个爬虫page.py是根据条件爬取符合条件的专利列表；<br>
>第二个爬虫detail.py则是根据第一个部分得到的专利列表爬取专利的具体信息。<br>
>相关说明<br>
>1. run_page.py 负责启动page爬虫(便于调试)；
>2. run_detail.py 负责启动detail爬虫(便于调试)；
>3. page爬虫使用了文件(checkpoint json格式文件)作为断点和队列，该文件由PersistParam类自动生成，当需要开启一个新的任务的时候，请删除原先的checkpoint文件；
>4. 当某一块爬取完成后，page爬虫检查队列是否有数据，有则设置断点，并开始爬取;
>5. 知网的搜索条件是得到cookie，相同的搜索条件对应的cookie是相同的;当出现验证码的时候进行重新请求cookie即可（也可以进行识别）
>6. hownet_config.py 提供了一些常用的知网搜索页面配置类，可根据条件自行添加和修改
>7. PersistParam.py 该文件主要负责遍历/files/pending/下的所有json格式文件，并把每一个字典作为一个请求。
##文件夹说明
>files/ 保存着待爬取文件，已爬取文件等 <br>
>files/page 保存了根据条件爬取到的html文件 <br>
>files/page_links 保存了根据条件爬取到并解析完成的json格式文件 <br>
>files/pending/ 保存着待爬取文件，需要搭配hownet_config.py下的配置类使用。[格式](#env)<br>
>files/html/ detail.py爬虫爬取到的详情页(html格式)保存路径 <br>
>files/detail detail爬虫爬取到的详情页(json格式)保存路径
## 配置文件
>### CNKIPaSearch.config
>该配置文件目前仅仅有一个变量，那就是PROXY_URL，用于提供代理：
>config.py
>```
>PROXY_URL = '127.0.0.1:5555/random'
>```
>代理目前主要是由Proxy类进行提供，同一时刻仅仅使用一个代理，当这个代理不可用的时候，才会重新进行请求
>### .env
>该文件由python-dotenv读取，python-dotenv会把该文件中的内容作为环境变量,比如：
>.env
>```
>CONFIG=ApplicantConfig
>```
>配置类在hownet_config.py文件中，它需要和请求队列的数据保持一致，以ApplicantConfig类为例：
>```
>class ApplicantConfig(BaseConfig):
>    """申请人配置"""
>    @staticmethod
>    def get_params(applicant):
>        params = {
>            "action": "",
>            "NaviCode": "*",
>            "ua": "1.21",
>            "isinEn": "0",
>            "PageName": "ASP.brief_result_aspx",
>            "DbPrefix": "SCPD",
>            "DbCatalog": "中国专利数据库",
>            "ConfigFile": "SCPD.xml",
>            "db_opt": "SCOD",
>            "db_value": "中国专利数据库",
>            "txt_1_sel": "SQR",
>            "txt_1_value1": applicant,
>            "txt_1_relation": "#CNKI_AND",
>            "txt_1_special1": "=",
>            "his": 0,
>            "__": BaseConfig._get_now_gmt_time()
>        }
>        return params
>```
>那么在使用ApplicantConfig类的同时，对应pending的文件格式为
>```
>[
>   {
>       "applicant": "东南大学"
>   },
>   ...
>]
>```
## 1.page爬虫
>### 1.1 思路
>run_page.py会开启爬虫
>page.py爬虫会判断checkpoint中队列中的数据(主分类号、申请人)，顺序爬取。
>爬虫在每次抓取页面成功后，会保存页面并解析页面，它也会判断当前的页面的专利个数。
>### 1.2 文件命名规范
>列表页命名 files/pending/中保存有待爬取的列表，以该列表的第一个元素为名称，文件名为页码(按照年份爬取的页面依次递增)
>比如
>```
>[
>   {
>       'applicant': '东南大学'
>   }
>]
>```
>则以东南大学作为文件夹的名称
>### 1.3 问题
>1. 目前的爬虫仅仅能爬取6000个数据，多的数据可以根据不同的搜索条件进行爬取
>2. [错误twisted.internet.error.TimeoutError: User timeout caused connection failure](https://blog.csdn.net/xiongzaiabc/article/details/89840730)
>3. 目前会根据环境中的config变量来获取到不同的配置文件
## 2.detail 专利[基础信息]爬虫
>### 2.1 思路
>run_detail.py可以开启detail爬虫,
>detail.py爬虫需要的格式如下(该格式可以由page爬虫生成)：
>```
>[
>   {
>       'dbcode': 'scpd',
>       'dbname': 'scpd年份',
>        'filename': 专利公开号
>   }
>   ,
>   //...
>]
>```
>该爬虫目前会遍历files/page_links/下的所有文件(级联文件夹)，并yield Request
>### 2.2 数据清洗
>数据可以保存到JSON/MongoDB中，同时，注意保证公开号的唯一
>目前有两个数据类型为数组：发明人和专利分类号(源数据用分号隔开)
>注：发明人 专利分类号 中间用分号隔开 就算只有一个也是用数组
>### 2.3 数据提取
>可以按照tr[style!='display:none']提取每一行，接着xpath('./td').extract()提取出
>该行所有的td
>```
>for td in tds:
>   if td.text() in self.mapping():
>       key = self.mappings()
>       value = td.next()
>       item[key] = value
>```
## Proxy
> 每个请求都会重试若干次以上（比如代理不可用等问题都会使得请求失败），同时会在最后一次尝试不再使用代理
>如果最后一次仍然失败，则将该出错记录下来。
## middleware
> GetFromLocalityMiddleware detail爬虫专属，在爬取之前会先判断本地是否存在对应的专利html文件
> RetryOrErrorMiddleware 重写最大值重试次数中间件 功能只是添加了一个日志输出 <br>
> ProxyMiddleware 使用requests库请求获取代理<br>
> CookieMiddleware page爬虫专用，设置cookie，会检测spider的cookie是否已经不可用，如果不可用，则重新发起请求获取 <br>
## pipeline
> SaveSearchJsonPipeline 用于把解析出来的搜索数据保存到json文件中<br>
> SaveSearchHtmlPipeline 保存原始的搜索页面 <br>
> FilterPipeline detail专属，用于过滤数据，更改数据格式 <br>
> SaveDetailHtmlPipeline 保存详细专利html页面到本地 <br>
> SaveDetailJsonPipeline 保存详细专利json数据到本地 <br>
> MongoPipeline 保存详细专利数据到mongo数据库 <br>
