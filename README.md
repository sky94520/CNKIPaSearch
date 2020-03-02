# 专利页面[非详情页]爬虫
>注：本项目为v2，第一版参见：[CrawlPage](https://github.com/sky94520/CrawlPage)<br>
>针对知网专利，本代码由两部分组成:
>第一部分是根据条件爬取符合条件的专利列表；
>第二部分则是根据第一个部分得到的专利列表爬取具体的专利。
>此为第一部分。
>相关说明<br>
>1. run_page.py 负责启动爬虫；
>2. 本爬虫使用了文件(checkpoint json格式文件)作为断点和队列；
>3. 当某一块爬取完成后，page爬虫检查队列是否有数据，有则设置断点，并开始爬取
>5. 知网的搜索条件是得到cookie，相同的搜索条件对应的cookie是相同的;当出现验证码的时候进行重新请求cookie即可（也可以进行识别）
## 思路
>run_page.py会开启爬虫
>page.py爬虫会判断checkpoint中队列中的数据(主分类号、申请人)，顺序爬取。
>爬虫在每次抓取页面成功后，会保存页面并解析页面，它也会判断当前的页面的专利个数。
## 文件命名规范
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
## 问题
>1. 目前的爬虫仅仅能爬取6000个数据，多的数据可以根据不同的搜索条件进行爬取
>2. [错误twisted.internet.error.TimeoutError: User timeout caused connection failure](https://blog.csdn.net/xiongzaiabc/article/details/89840730)
>3. 目前会根据环境中的config变量来获取到不同的配置文件
## 所需外部环境
## middleware
> 代理，会发送请求requests获取代理
> 设置cookie，会检测spider之前的cookie是否已经不可用，如果不可用，则重新发起请求获取
> 重写最大值重试次数中间件 功能只是添加了一个日志输出
## pipeline
> JsonPipeline 用于把解析出来的数据保存到json文件中<br>
> SavePagePipeline 保存原始的页面
