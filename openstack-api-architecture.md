# OpenStack API 架构
OpenStack是开源的IaaS解决方案，完全由python实现，由apache协议发行，被称为云计算界的Linux。

由于需要适应不同企业的需求，一个灵活可扩展的架构尤其重要，其中API扩展性更是重中之重。
OpenStack内组件繁多，架构也各有不同，本文仅介绍OpenStack项目中常见的API架构，主要参考组件为Nova，Cinder，Glance，并且介绍API的扩展方法。同时本文描述的架构也十分有利于理解其他组件的API实现。

## WSGI协议
WSGI（Python Web Server Gateway Interface），是为Python语言定义的Web服务器和Web应用程序或框架之间的一种简单而通用的接口。WSGI包括两方面：一为“服务器”或“网关”，另一为“应用程序”或“应用框架”。在处理一个WSGI请求时，服务器会为应用程序提供环境及一个回调函数（Callback Function）。当应用程序完成处理请求后，通过回调函数，将结果回传给服务器。

一个简单的“WSGI应用程序”需要实现以下接口：

```
  def app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    yield "Hello world!\n"
```

其中:

  * 第一行定义了一个名为app的callable，接受两个参数，environ和start_response，environ是一个字典包含了CGI中的环境变量，start_response也是一个callable，接受两个必须的参数，status（HTTP状态）和response_headers（响应消息的头）。
  * 第二行调用了start_response，状态指定为“200 OK”，消息头指定为内容类型是“text/plain”
  * 第三行将响应消息的消息体返回。


按照WSGI的接口可以很轻松的实现一个可扩展的框架。如，我们将实现一个核心app和一个用户验证中间件（过滤器）。

  * 核心app的功能是输出“hello netease”
  * 用户验证中间件的功能是验证用户请求的Header是否带有合法的X-Auth-Token

代码如下：

```
import eventlet
from eventlet import wsgi

# 核心app，输出"helo netease"
def core_app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return "hello netease"


# 验证用户请求中间件，判断用户请求的Header中X-auth-token是否等于“openstack”
# 如果验证通过则跳转至core_app；否则返回401 Unauthorized，请求处理结束；

def authorize(environ, start_response):
    if environ['HTTP_X_AUTH_TOKEN'] == 'openstack':
        return core_app(environ, start_response)
    else:
        start_response('401 Unauthorized', [('Content-Type', 'text/plain')])
        return '401 Unauthorized'


wsgi.server(eventlet.listen(('', 8090)), authorize)
```

OpenStack所有组件高度服务化，通过提供RESTFul API的形式向外提供服务，所以OpenStack是一个“WSGI应用程序”。同时OpenStack为了方便部署，依赖于eventlet实现的wsgi.server，无需另外安装“WSGI服务器”。直接运行服务即可处理用户的API请求。OpenStack的所有API都要通过keystone验证用户请求是否合法，其中实现原理归根到底就是以上例子。

## paste deploy
按照WSGI协议，WSGI应用程序可以相互关联，组成一个stack或者pipeline的模式。即一个pipeline由若干个middleware（filter）和一个app组成。用户请求依次经过middleware，最终交由app处理。并且app的响应结果也逆序依次经过middleware。如下图所示：

<img src="http://blog.ez2learn.com/wp-content/uploads/2010/01/pylons_as_onion.png"/>

洋葱层层包裹，最里层是core app，外部包裹着middleware，请求先由最外层的middleware处理，到中间的core app，当core app处理完核心业务逻辑，响应体先经过最里层middleware， 最后经过最外层的middleware。

[Paste Deploy](http://pythonpaste.org/deploy/)是python的一个第三方库，使用此库能方便地从配置文件生成一个stack。

在Paste Deploy中有主要有三个概念：pipeline，filter，app。其中`pipeline`由若干filter和一个app组成。`filter`是一个过滤器，也叫middlereware，对请求做过滤，或者修改响应。`app`是核心应用，执行主要业务逻辑。

将上文的示例代码用paste deploy配置文件描述：

```
[pipeline:openstack]
pipeline = authtoken core_app

[app:core_app]
paste.filter_factory = CoreApp.factory

[filter:authtoken]
paste.filter_factory = Authorize.factory
admin_pass = openstack
```

其中，`pipeline:openstack` 指明这是一个名字为openstack的pipeline，它由两部分组成，名为authtoken的filter，及名为core_app的app。其中`filter:authtoken`带了其他配置，如`admin_pass`设置为openstack。这些配置信息将传递给Authorize.factory方法，因此可以动态生成对应的authorize方法。

具体到OpenStack项目中，`app`主要实现IaaS的相关业务，比如提供虚拟机操作API，云硬盘操作API等。一些通用的功能，如token的验证，访问频率限制等，这些功能各模块都需要，所以可以做成通用的模块，以filter的形式包裹在app外层。

##扩展方法
扩展paste deploy十分方便，首先实现对应的filter代码，然后修改deploy配置文件即可。

举例：完成一个filter，此filter将所有URI为`/nt_version`的请求拦截，并且返回软件的版本号。

代码如下：

File: nt_version.py
```
def filter_factory(global_config, **local_config): 
    version = local_config['version']
    def reporter(app):
        return ReportVersionFilter(app, version)
    return reporter
  
class ReportVersionFilter(object):
    def __init__(self, app, version):
        self.app = app
        self.version = version

    def report_version(env, start_response):
        headers = [('Content-Type', 'application/json')] 
        start_response('200 OK', headers)
        return self.version
        
    def __call__(self, env, start_response):
        if env['PATH_INFO'] == '/nt_version':
            return report_version_app(env, start_response)
        else:
            return self.app(env, start_response)
```

配置文件如下：
```
....

[pipeline:osapi_compute]
pipeline = nt_version authtoken core_app

[filter:nt_version]
paste.filter_factory = nt_version.filter_factory
version = 0.11
```

代码很简单，PasteDeploy读取完配置文件，当要生成osapi_compute pipeline时，由于新加了`nt_version` filter，会通过配置调用nt_version.filter_factory,并将其他配置信息传递给filter_factory。

`ReportVersionFilter`作为一个Filter，做完过滤处理后可能需要交由之后的app，后者之后的filter继续处理，所以第一个参数接收PasteDeploy传递的app。第二个参数`version`是业务相关的，可以任意定义，这里我们通过配置文件定义软件版本号，所以在配置文件中指定。

`__call__`是标准WSGI实现，主要逻辑是判断URI是否为`nt_version`，是则返回软件版本号，否则交由下一个app继续处理。


通过PasteDeploy可以对OpenStack的API做任意的扩展，比如可以根据特征屏蔽特定请求，以防御DDOS攻击；可以为API增加Cache层；可以对API增加Gzip支持；可以将响应体加入特定信息等。希望本文能够起到抛砖引玉的作用，让读者扩展一些对OpenStack扩展的思路。

