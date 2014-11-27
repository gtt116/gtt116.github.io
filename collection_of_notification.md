# 通知消息（notification）收集

## 背景
目前NVS服务的状态主要通过运维平台的进程数量监控，日志监控，服务状态检查来保证，这些监控方法由于将系统看成黑盒从而都有一些问题。
* 进程数量监控：无法应对进程虽在，但是进程卡死的问题
* 服务状态监控：站在用户角度，将服务看成是黑盒，无法直观的获取服务内部状态。比如：虽然创建虚拟机成功了，但是其实经过了几次重调度，此时服务状态监控无法发现问题。
* 日志监控：
  无法应对进程虽在，但是进程卡死的问题；信息过于底层，对于请求在服务之间的传递不直观。比如创建失败的TRACE信息只能判断此节点上出了什么问题，要判断这个请求是哪个服务传递过来，发送请求的用户是谁很费时费力。

## 通知消息收集可以用来干嘛

通知消息(notification)是OpenStack服务中普遍使用的，通过消息队列暴露内部信息的方法。可以用来计费，监控以及定位问题，判断服务SLA等。

收集并分析消息，我们可以：

* 监控系统运行状况：通知消息包含**是否发生异常**，**异常是什么**，通过统计和分析，可以检测服务的稳定性，比如哪些节点的error消息很多，则可能出问题。
* 实时监控用户请求：通过通知消息我们可以知道：一个用户在**什么时候**发送了**什么请求**，请求经过了**哪些节点**，请求**什么时候开始** **什么时候结束**，请求的**所有参数**是什么。
* 判断SLA；比如统计平台从上线到现在**一共处理了多少次创建虚拟机请求**，平均处理时间是多少，每个服务占用多少时间，每个子请求占了多少时间，发生了多少次异常，这些异常都是哪些节点，哪些异常等。
* 为优化服务提供线索，比如创建虚拟机过程中的下载镜像子请求占了绝大多数时间，那么可以确定未来优化方向。
* 快速定位问题，用户提供tenant-id，或者request-id，我们可以快速找到请求经过了哪些服务，哪个节点上出现了异常，具体异常是什么。并且很快知道用户之前做了哪些操作，为定位问题提供线索。

## 什么时候会产生通知信息
* 任何**增删改**操作都会触发通知，对于比较复杂的操作，会将每一子请求的开始和结束分别触发消息，比如：compute.instance.resize.start/.end，compute.instance.pre_resize.start/.end, compute.instance.finish_resize.start/.end
* 每天的资源使用情况会触发一次消息，比如：已存在的虚拟机每天会触发一次 “compute.instance.exists”，通知中包含虚拟机的基本信息，如flavor，image，port等。
* 系统发生异常，会产生error通知。正常情况下通知发送到notification.info中，异常的消息会发送到notification.error中

### 消息类型
消息包括正常请求处理情况以及定时任务产生的状态信息。

请求处理消息会通过X.start,X.end标记开始和结束，如果发生错误会产生X.error消息比如：
* compute.instance.create.{start,error,end}
* compute.instance.delete.start/.end
* compute.instance.rebuild.start/.end
* compute.instance.resize.prep.start/.end
* compute.instance.resize.confirm.start/.end
* compute.instance.resize.revert.start/.end
* compute.instance.shutdown.start/.end
* compute.instance.power_off.start/.end
* compute.instance.power_on.start/.end
* compute.instance.snapshot.start/.end
* compute.instance.resize.start/.end
* compute.instance.finish_resize.start/.end
* volume.create.start/.end
* volume.delete.start/.end
* ...

定时任务消息会汇报资源的具体使用情况，如：
* compute.instance.exists
* compute.instance.update
* 。。。

### 支持通知消息的服务
由于notification的实现逻辑在oslo中，所以OpenStack项目中所有组件理论上都支持通知消息。目前比较成熟的有：
* nova
* glance
* keystone
* cinder
* neutron
* heat
* ceilometer
* ...

### 相关开源项目
* [stacktach](https://github.com/rackerlabs/stacktach) rackspace
* [yagi](https://github.com/rackerlabs/yagi) rackspace


### 消息示例
```json
{"event_type": "compute.instance.resize.confirm.start",
 "timestamp": "2012-03-12 17:01:29.899834",
 "message_id": "1234653e-ce46-4a82-979f-a9286cac5258",
 "priority": "INFO",
 "publisher_id": "compute.compute-1-2-3-4",
 "payload": {"state_description": "",
            "display_name": "testserver",
            "memory_mb": 512,
            "disk_gb": 20,
            "tenant_id": "12345",
            "created_at": "2012-03-12 16:55:17",
            "instance_type_id": 2,
            "instance_id": "abcbd165-fd41-4fd7-96ac-d70639a042c1",
            "instance_type": "512MB instance",
            "state": "active",
            "user_id": "67890",
            "launched_at": "2012-03-12 16:57:29",
            "image_ref_url": "http://127.0.0.1:9292/images/a1b2c3b4-575f-4381-9c6d-fcd3b7d07d17"}}
            
{"event_type": "compute.instance.create.end",
 "timestamp": "2012-03-12 17:00:24.156710",
 "message_id": "00004e00-8da5-4c39-8ffb-c94ed0b5278c",
 "priority": "INFO",
 "publisher_id": "compute.compute-1-5-6-7",
 "payload": {"state_description": "",
             "display_name": "testserver",
             "memory_mb": 512,
             "disk_gb": 20,
             "tenant_id": "12345",
             "created_at": "2012-03-12 16:58:32",
             "instance_type_id": 2,
             "instance_id": "abcdef01-7b76-4b43-9143-fb2385df48a3",
             "instance_type": "512MB instance",
             "state": "active",
             "user_id": "67890",
             "fixed_ips":
                 [{"floating_ips": [],
                   "meta": {},
                   "type": "fixed",
                   "version": 6,
                   "address": "fe80::1234:5678"},
                  {"floating_ips": [],
                   "meta": {},
                   "type": "fixed",
                   "version": 4, "address": "127.0.1.1"},
                  {"floating_ips": [],
                   "meta": {},
                   "type": "fixed",
                   "version": 4,
                   "address": "10.180.0.151"}],
             "launched_at": "2012-03-12 17:00:23.998518",
             "image_ref_url": "http://127.0.0.1:9292/images/12345678-201f-4600-b5a1-0b97e2b1cb31"}}
```

## 参考
* https://wiki.openstack.org/wiki/SystemUsageData
* http://www.sandywalsh.com/2013/09/notification-usage-in-openstack-report.html
