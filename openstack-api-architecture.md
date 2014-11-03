# OpenStack API 架构
OpenStack是开源的IaaS解决方案，完全由python实现，由apache协议发行，被称为云计算界的Linux。

由于需要适应不同企业的需求，一个灵活可扩展的架构尤其重要，其中API扩展性更是重中之重。
OpenStack内组件繁多，架构也各有不同，本文仅介绍OpenStack项目中常见的API架构，主要参考组件为Nova，Cinder，Glance，并且介绍API的两种扩展方法。同时本文描述的架构也十分有利于理解其他组件的API实现。

## WSGI协议
WSGI（Python Web Server Gateway Interface），是为Python语言定义的Web服务器和Web应用程序或框架之间的一种简单而通用的接口。WSGI包括两方面：一为“服务器”或“网关”，另一为“应用程序”或“应用框架”。在处理一个WSGI请求时，服务器会为应用程序提供环境及一个回调函数（Callback Function）。当应用程序完成处理请求后，通过回调函数，将结果回传给服务器。

OpenStack所有组件高度服务化，通过提供RESTFul API的形式向外提供服务，所以OpenStack是一个“WSGI应用程序”。同时OpenStack为了方便部署，依赖于eventlet实现的wsgi.server，无需另外安装“WSGI服务器”。直接运行服务即可处理用户的API请求。

## paste deploy扩展

## OpenStack API 扩展
