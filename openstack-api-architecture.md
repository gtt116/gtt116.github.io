# OpenStack API 架构
OpenStack是开源的IaaS解决方案，完全由python实现，由apache协议发行，被称为云计算界的Linux。

由于需要适应不同企业的需求，一个灵活可扩展的架构尤其重要，其中API扩展性更是重中之重。
OpenStack内组件繁多，架构也各有不同，本文仅介绍OpenStack项目中常见的API架构，主要参考组件为Nova，Cinder，Glance，并且介绍API的两种扩展方法。同时本文描述的架构也十分有利于理解其他组件的API实现。

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

## paste deploy扩展

## OpenStack API 扩展
