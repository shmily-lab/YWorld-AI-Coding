# -*- coding: utf-8 -*-
"""
求职工作台生成器
整合三块数据：
  1. 邮件追踪待办（测评/笔试/面试/投递）
  2. 已投递公司校招官网（来自 build_campus_sites.DATA）
  3. 尚未投递、仍开放的 2027 届大厂校招通道
"""
import sys, os, json, datetime

OUT_DIR = r"D:\y'world\求职邮件追踪"
sys.path.insert(0, OUT_DIR)
import build_campus_sites as bcs  # 复用其 DATA / APPENDIX

TODAY = datetime.date(2026, 9, 26)

# ---------- 1. 待办（来自邮件追踪） ----------
# type, 公司, 事项, 截止(datetime str), 链接, 备注
TODOS = [
 ("笔试", "京东集团", "2027校招-安全工程师试卷-0926（100分钟，全程摄像头）", "2026-09-26 11:40",
  "https://hr.nowcoder.com/v1/s/tz6lJ1yl#", "开考 09-26 10:00；最新版 Chrome，提前15分钟调试设备；每项目仅3次笔试机会"),
 ("测评", "携程集团", "SRE工程师（2027届秋招）能力测评，约40分钟", "2026-09-28 23:59",
  "https://ctrip.ceping.com/Login/Elink?elink=VsIbc825DTDFqJfb6d5NC6lFNe7CbaMzxcChina25xBDBsULNnUzcf95Hayo6wX984A==",
  "09-24 11:12 收到，3个工作日内；全程开摄像头、关微信QQ、勿用校园网"),
 ("投递", "米哈游 miHoYo", "岗位投递邀请（3天内有效）", "2026-09-26 23:59",
  "https://jobs.mihoyo.com/#/campus/position?invitationToken=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJuYmYiOjE3OTAxNDI3NDE2OTIsImJpel90eXBlIjoicmVzdW1lX2ludml0YXRpb24iLCJpc3MiOiJhdHNfcmVjcnVpdCIsImV4cCI6MTc5MTM1MjM0MTY4MCwiYml6X2lkIjo3OTAzMiwiaGlyZV90eXBlIjoxLCJpYXQiOjE3OTAxNDI3NDE2OTJ9.CCqXxYSTQFOKJSr2S7gubtqw3_J7qIFle8CWTu9KufM",
  "应届生仅能投1个职位；校招官网 jobs.mihoyo.com"),
 ("测评", "深圳市卓驭科技", "综合素质测评（60~90分钟）", "2026-09-29 14:38",
  "https://zyt-hr.ceping.com/pc?aId=WyI92zBn/dfIAqlMhDSVlA==", "通行证 64262624912180；需开音视频，仅1次机会"),
 ("活动", "智联招聘", "秋招双选会报名（名企综合场 + 珠三角场）", "2026-09-30 23:59",
  "", "智联招聘 App / 站内「不设限秋招节 3.0」"),
 ("测评", "汇川技术", "27校招-联合动力 IT安全/基础设施工程师测评（20~40分钟）", "2026-10-01 23:59",
  "https://recruit.inovance.com/eap/#/assessment?candidate=a-6a627fce-0a4d-44be-beb2-14b2fec0c16a", "09-17 收到"),
 ("测评", "新华三技术", "测试工程师(J18862) 在线测评", "2026-10-03 00:25",
  "https://h3c.ceping.com/pc?aId=rw5/jb8piton86E1gpw8Ig==", "通行证 12261871752329"),
 ("简历", "新华三技术", "完善简历信息（测试工程师岗位）", "2026-10-03 23:59",
  "https://bsurl.cn/v2/qbUni4rQ", "测评与简历两件事分开，别只做一件"),
 ("投递", "途虎养车", "改一版简历适配「测试开发工程师」（2027届校招）并投递", "2026-09-30 23:59",
  "https://www.tuhu.cn/",
  "截止 09-30 24:00；推荐以「运维版」简历为底改（JD匹配度约60–65%），主打 AI 赋能测试：AI测试体系/平台搭建、用AI工具辅助测试、了解大模型基本能力；别拖到截止当天再投"),
]

# 无明确截止的待处理事项
PENDING = [
 ("简历", "恒生招聘", "邀请更新简历（原截止 09-23 24:00 已过，建议主动补登）", ""),
 ("简历", "卓望校招组", "简历信息完善（两个链接）", "https://bsurl.cn/v2/DuJNT4f9　／　https://bsurl.cn/v2/9uXCXhCm"),
 ("问卷", "正浩 EcoFlow", "实习意向收集问卷（SRE 岗要求提前到岗实习）", ""),
 ("问卷", "途游游戏", "游戏经历补充问卷（⚠️ 链接已失效：09-26 核验返回「链接无效或已过期」；且途游已判未通过，此项可弃）", ""),
 ("系统", "宇视科技", "招聘系统账号：用户名 PC_568655", "https://talent.uniview.com/wt/uniview/web/index?brandCode=uniview"),
 ("群", "恒生电子", "校招交流 QQ 群 1047909224（验证答案 600570）", ""),
]

# ---------- 2. 已结束 / 未通过（来自邮件追踪） ----------
# 类别, 公司, 岗位/事项, 时间, 说明
DEAD = [
 ("未通过", "联想中国", "IT运维工程师（深圳）/ 运维开发工程师（天津）", "09月", "简历/测评未通过"),
 ("未通过", "SHEIN 希音", "IT运维实习生（南京）", "09月", "未通过"),
 ("未通过", "Shopee", "SRE（运维）工程师-深圳", "09月", "未通过"),
 ("未通过", "库洛游戏", "游戏测试工程师", "09月", "未通过"),
 ("未通过", "爱立信", "无线网络优化工程师（南京）/ 无线网络工程师（重庆）", "09月", "未通过"),
 ("未通过", "锐捷网络", "安全研发工程师-防火墙（成都）", "09月", "未通过"),
 ("未通过", "极兔速递", "网络管理管培生、信息安全管培生", "09月", "未通过"),
 ("未通过", "途游游戏", "运维工程师（北京）", "09月", "未通过（另需补游戏经历问卷）"),
 ("未通过", "豪迈集团", "运维工程师（山东）", "09月", "测评后未通过"),
 ("未通过", "通号低空", "通信工程师", "09月", "无回应"),
 ("未通过", "上海甄汇（汇联易）", "交付业务顾问-广州-中文（复试 09-21）", "09-22", "复试未通过"),
 ("已考", "恒生电子", "运维工程师 在线笔试", "09-23 19:00", "已考，等结果"),
 ("已考", "FunPlus 趣加", "27校招-测试工程师 笔试", "09-19 16:00", "已考，等结果"),
 ("已过期", "泸州老窖", "2027届全国校招测评", "09-20", "已过期"),
 ("已过期", "宇视科技", "算法测试工程师(济南) 测评", "09-18", "已过期"),
 ("已过期", "中国建筑", "校招第一轮测评", "09-17", "已过期"),
 ("已过期", "腾讯", "综合素质测评（2×30min，48h）", "09-16", "已过期，48小时窗口"),
 ("已过期", "京东 JDS", "2027 JDS 测评（45min）", "09-16", "已过期"),
 ("已过期", "京东 JD YOUNG", "实习生计划测评（45min）", "09-16", "已过期"),
 ("已过期", "国家开发银行", "测评（72h）", "09-16", "已过期；但校招报名通道 10-07 才关，可重投"),
 ("已过期", "中国中化", "图灵计划 网络安全工程师测评", "09-19", "已过期"),
 ("已过期", "东风汽车", "信息安全-联友科技测评", "—", "大概率过期"),
 ("已过期", "小米", "校招测评（30~45min，72h）", "09-13", "已过期"),
 ("已过期", "奔图科技", "校招测评", "约09-13", "已过期"),
 ("已过期", "海康威视", "校招在线测评（7天）", "09-17", "已过期"),
 ("已过期", "欣旺达", "网络工程师测评", "09-11", "已过期"),
 ("已过期", "卓望公司", "运维工程师-深圳 笔试（30min，3天内）", "09-23", "已过期"),
]

# ---------- 3. 尚未投递、仍开放的大厂校招通道 ----------
# name, cat, fit(high/mid/low), url, deadline, note
NEW = [
 # 互联网 / 科技
 ("拼多多","互联网/科技","high","https://careers.pddglobalhr.com/campus","2027-01-31","正式批9月2日已开，研发类含安全工程师，3000+ offer，招满即止"),
 ("哔哩哔哩 B站","互联网/科技","high","https://jobs.bilibili.com/campus/positions","","技术类明确有 SRE 工程师岗，最多投2个志愿"),
 ("知乎","互联网/科技","high","https://app.mokahr.com/campus_apply/zhihu/68321","","含大模型安全研究员、爬虫安全、测试开发方向"),
 ("华为","互联网/科技","high","https://career.huawei.com/cn/campus-recruitment.html","","8月15日启动，研发类含网络/网络安全方向，官网为唯一入口"),
 ("中兴通讯 ZTE","互联网/科技","high","https://job.zte.com.cn","","岗位含网络安全工程师、网络技术工程师，网申无截止但岗位有限"),
 ("英伟达 NVIDIA 中国","互联网/科技","high","https://app.mokahr.com/campus-recruitment/nvidia/47111","","7月20日开启，软件类含云存储基础设施、AI基础设施、机器学习运维"),
 ("特斯拉","互联网/科技","high","https://app.mokahr.com/campus-recruitment/tesla/41460","","9月开放网申，软件类含「基础架构」「运维/技术支持」方向"),
 ("荣耀 HONOR","互联网/科技","mid","https://www.honor.com/cn/career/","2026-09-30","8大类岗位含「流程IT与质量运营类」，本硕简历投递9月30日24:00截止"),
 ("浪潮集团","互联网/科技","mid","http://career.inspur.com/campus2027/index.html","","技术类含测试、实施、数据中心专业工程师"),
 ("京东物流","互联网/科技","mid","https://campus.jd.com","2026-11-30","「新锐之星」独立项目，入口在京东校招官网 + 京东物流招聘公众号"),
 ("微博（新浪&微博）","互联网/科技","mid","https://app.mokahr.com/social-recruitment/sina/43535?locale=zh-CN#/","","2027届技术专场含系统开发/测试开发工程师（测试开发对口你的测试方向），未见专门运维/安全岗；官网 career.sina.com.cn"),
 ("OPPO","互联网/科技","low","https://careers.oppo.com/university/oppo/campus","","11大类以软硬研发为主，未见独立运维/安全类，招满即止"),
 ("大疆 DJI","互联网/科技","low","https://careers.dji.com/zh-CN/campus","","「拓疆者」6月25日开启，不设截止、招满即止，限投1个职位"),
 ("微软中国","互联网/科技","low","https://careers.microsoft.com/","2026-10-08","APRD 网申至10月8日23:59，仅 Software Engineer 等研发岗"),
 ("亚马逊中国","互联网/科技","low","https://www.amazon.jobs/content/en/career-programs/university","","8月24日开启，岗位为 SDE / 解决方案架构师，未见独立运维安全岗"),
 ("IBM 中国","互联网/科技","low","https://www.ibm.com/careers/","","无中国区独立校招页，需在官方招聘站内筛选应届生岗（含IT咨询、基础架构）"),
 # 网络安全厂商
 ("安恒信息","网络安全","high","https://ahzp.dbappsecurity.com.cn/","","校招进行中，含安全分析、Agent 智能安全运营，杭州滨江总部，滚动筛选"),
 ("亚信安全","网络安全","high","https://asiainfo-sec.jobs.feishu.cn/campus","2026-10-30","AI类/研发/测试/安全研究员，覆盖9城，全岗免笔试，每人限投1岗"),
 ("启明星辰","网络安全","high","https://venustech2.zhiye.com/campus/jobs","2027-06-30","开发/测试/产品类，北京成都杭州，北京户口指标倾斜"),
 ("长亭科技","网络安全","high","https://join.chaitin.cn/","","AI研发/AI攻防/安全研究/FDE/解决方案，8月起滚动开放，简历可投 resume@chaitin.com"),
 ("三六零 360","网络安全","high","https://360campus.zhiye.com/campus/jobs","","2027全球校招已开，安全研究/算法/开发/大数据，10月10日首批笔试"),
 ("天融信","网络安全","mid","https://www.topsec.com.cn/hr/campus.html","","官方校招页 + 「天融信招聘」公众号，2027届是否开放需进页面确认"),
 ("山石网科","网络安全","mid","https://hillstonenet.zhiye.com/campus/jobs","","8月24日启动，售前/售后工程师，流程网申→笔试→测评→面试"),
 ("美亚柏科","网络安全","mid","https://www.iguopin.com/job/detail?id=217598888373126605","2027-06-30","国投旗下，算法/AI开发/售前解决方案，厦门北京"),
 ("斗象科技","网络安全","mid","https://www.tophant.com/about","","AI安全顶尖人才校招，无独立网申系统，简历发 zhaopin@tophant.com"),
 ("格尔软件","网络安全","low","https://www.koal.com","","2027届目前开放的是长期技术实习（C++/Java/测试，西安上海），投递 xiyan-zp@koal.com"),
 # 金融 / 运营商 / 电网
 ("中国移动（集团）","金融/运营商/电网","high","https://job.10086.cn","","省公司+专业公司大量招通信/网络/IT/信息安全岗，统一笔试10月24日，各省截止不同"),
 ("中国联通（集团）","金融/运营商/电网","high","https://zglt.iguopin.com","","8月底开放、无统一截止，统一笔试11月上旬，招网络安全、算网、IT研发类"),
 ("招商银行","金融/运营商/电网","high","https://career.cmbchina.com/","2026-10-10","总行信息技术部 + 各分行科技岗，规模大；信用卡中心已投，银行本体是独立通道"),
 ("中国建设银行","金融/运营商/电网","high","http://job.ccb.com","2026-10-08","运营数据中心招网络运维、信息安全；总行+37家分行合计万人级"),
 ("中国农业银行","金融/运营商/电网","high","https://career.abchina.com.cn/","2026-10-08","研发中心/数据中心信息科技岗，含网络与信息安全方向"),
 ("交通银行","金融/运营商/电网","high","https://job.bankcomm.com","2026-10-18","金融科技条线招 IT系统管理、安全技术、数据安全，信息科技类约500人"),
 ("中国邮政储蓄银行","金融/运营商/电网","high","https://psbc2027.zhaopin.com","2026-10-07","总行信息科技岗（软件开发、运维、信息安全）+ 各省分行科技岗"),
 ("兴业银行","金融/运营商/电网","high","https://job.cib.com.cn/","2026-10-25","科技专项招人工智能、运维方向，明确要网络工程/信息安全专业"),
 ("中国铁塔","金融/运营商/电网","mid","https://zhaopin.chinatowercom.cn","2026-10-27","总部及省分公司信息化岗，招信息技术/通信网络/运维类"),
 ("中信银行（总行）","金融/运营商/电网","mid","https://job.citicbank.com","2026-10-09","总行信息技术岗/软件开发中心，独立于已投的信用卡中心通道"),
 ("浦发银行","金融/运营商/电网","mid","https://job.spdb.com.cn","2026-10-08","总行科技储备生、信息科技岗（开发/运维/安全），10月8日18:00截止"),
 ("中国民生银行","金融/运营商/电网","mid","https://career.cmbc.com.cn/","2026-10-25","「扬帆/启航」计划科技方向，总行信息科技部招开发、运维、数据安全"),
 ("宁波银行","金融/运营商/电网","mid","https://zhaopin.nbcb.com.cn","2026-10-31","总行科技部明确招计算机、网络工程、信息安全专业，城商行科技投入高"),
 ("杭州银行","金融/运营商/电网","mid","https://myjob.hzbank.com.cn","2026-10-25","信息科技岗（开发、运维、数据安全、网络）"),
 ("中广核","金融/运营商/电网","mid","https://www.cgnpc.com.cn/","2026-10-30","含信息安全、仪控/数字化（DCS、工业网络）类岗位"),
 ("中国电科 CETC","金融/运营商/电网","mid","https://www.cetc.com.cn","","各研究所自主发布（如29所截止2027-05-11），大量招网络空间安全、通信类"),
 ("国家电网","金融/运营商/电网","low","https://zhaopin.sgcc.com.cn","","第一批公告预计11月中旬；信通提前批见 campus.51job.com/SGIT2027/（10月底截止）"),
 ("南方电网","金融/运营商/电网","low","https://zhaopin.csg.cn","","正式批网申预计11月初；南网数字集团提前批招信息通信类约170人"),
 ("中国银联","金融/运营商/电网","low","https://join.unionpay.com/wt/unionpayhr/web/index","","含技术开发、信息安全、系统运维类岗，2027届公告待公众号通知"),
 # 制造 / 半导体 / 汽车
 ("京东方 BOE","制造/半导体/汽车","high","https://campus.boe.com/","","信息技术类明确列 IT运维、信息安全、CIM系统实施、数据治理，最对口的一批"),
 ("蔚来","制造/半导体/汽车","high","https://campus.nio.com","","数字技术类下明确设「技术运维」「数字安全」岗位，高度对口"),
 ("比亚迪","制造/半导体/汽车","high","https://job.byd.com/portal/mobile/school-home","","8月19日启动，需求含计算机类、网络空间安全，岗位含网络安全、信息化平台开发"),
 ("长江存储","制造/半导体/汽车","high","https://ymtc.zhiye.com/","","8大职位类别明确含「信息技术类」，每人最多投3个志愿"),
 ("长鑫存储","制造/半导体/汽车","high","https://cxmt.zhiye.com/campus/jobs","2026-09-30","7大岗位类别含「信息技术类」，官方校招日历标注9月30日24:00网申截止"),
 ("寒武纪","制造/半导体/汽车","high","https://app.mokahr.com/campus-recruitment/cambricon/44201","","「工程效率研发工程师」负责 CI/CD、云原生架构、自动化运维"),
 ("吉利控股","制造/半导体/汽车","high","https://campus.geely.com","2026-10-31","九大岗位类别明确含「IT/互联网类」，网申8/13—10/31"),
 ("TCL","制造/半导体/汽车","high","https://campus.tcl.com/","","岗位类别含「信息技术类」，下属公司 IT 类直接写明招信息安全、网络工程专业"),
 ("美的集团","制造/半导体/汽车","mid","https://careers.midea.com/","","八大职类明确含「信息技术类」，另有应届博士与实习生通道"),
 ("格力电器","制造/半导体/汽车","mid","https://zhaopin.greeyun.com/home","","7大类含「信息技术类」，限投1个岗位，投递后不可更改"),
 ("海尔智家","制造/半导体/汽车","mid","https://maker.haier.net/smart_home","","岗位大类含「计算机IT类」，软件研发类下设 IT 产品经理"),
 ("立讯精密","制造/半导体/汽车","mid","https://luxshare.hotjob.cn/","","八类岗位含「IT岗」，华南/华东分园区，最多投2个岗位"),
 ("长安汽车","制造/半导体/汽车","mid","http://changan.zhiye.com/Campus","","十大岗位方向含「数字化技术类」，智能网联涉及信息安全；网申后需完成AI测评"),
 ("上汽集团","制造/半导体/汽车","mid","https://saic-recruit.saicmotor.com","","31家所属企业联合招聘，岗位明确含「信息系统」类"),
 ("宁德时代","制造/半导体/汽车","low","https://app.mokahr.com/campus-recruitment/catlhr/148948","","6大职类含「计算机与AI类」，未见独立IT运维或信息安全职类"),
 ("理想汽车","制造/半导体/汽车","low","https://www.lixiang.com/employ/campus/list.html","","10大职类以算法与软件、芯片研发为主，未见独立IT/信息安全类"),
 ("小鹏汽车","制造/半导体/汽车","low","https://campus.xiaopeng.com","","「探索者计划」13大岗位，官网未设截止、招满即止"),
 ("赛力斯","制造/半导体/汽车","low","https://sokon.zhiye.com/campus","","6大类岗位，研发类含软件&系统开发，未见独立IT运维类"),
 ("广汽集团","制造/半导体/汽车","low","https://xyzp.51job.com/gacgroup2027","","9大岗位方向未单列IT类，但有智联系统验证、测试等计算机向岗位"),
 ("地平线","制造/半导体/汽车","low","https://horizon-campus.hotjob.cn/","2026-10-30","招聘方向为算法/芯片/软件/硬件/测试，无独立IT运维或信息安全岗"),
 ("紫光展锐","制造/半导体/汽车","low","https://www.unisoc.com/","","11类岗位以芯片/软件/算法为主，软件类可能含IT岗"),
]

UNCONFIRMED = [
 ("诺基亚贝尔","互联网/科技","未检索到中国区 2027 届校招官方入口，仅有诺基亚全球招聘页"),
 ("知道创宇","网络安全","未查到官方校招入口，建议走 knownsec.com「加入我们」或公众号"),
 ("盛邦安全","网络安全","仅见2026届简章，2027届建议盯「盛邦安全招聘」公众号"),
 ("永信至诚","网络安全","无2027届公告，官网加入我们页与邮箱 yxzhaopin@integritytech.com.cn 可自荐（偏社招）"),
 ("卫士通","网络安全","51job 校招专页未标注届别且多要求硕博，建议先邮件 HR@westone.com.cn 确认"),
 ("中孚信息","网络安全","官网未见2027届公告，公开信息只有27届实习岗（技术支持类）"),
 ("北信源","网络安全","诚聘英才板块无2027届校招入口，在招以社招/驻场运维为主"),
 ("任子行","网络安全","招贤纳士页未标注届别，校招曾覆盖2026/2027届，需电话或邮件确认"),
 ("飞天诚信","网络安全","官网无2027届校招入口，招聘邮箱 recruit@ftsafe.com"),
 ("云智慧","网络安全","官网仅列社招岗与邮箱 hr.hiring@cloudwise.com，无校招通道"),
 ("博睿数据","网络安全","官网无2027届校招入口，高校就业网仅单位介绍"),
 ("中国光大银行","金融/运营商/电网","未检索到2027届官方校招公告与投递入口，建议盯官网人才招聘栏与公众号"),
]

# ---------- 内推码 ----------
# (公司, 内推码(多个用 / 分隔), 分类, 投递链接, 可信度, 备注)
# 可信度: high=高校就业网/官方简章  mid=牛客员工帖  low=聚合帖·未验证
REF = [
 # —— 互联网 / 科技 ——
 ("腾讯","TECCED77Z1 / UF5SDOR1CY / E3HGVSFMCK / ASZH3IB8","互联网/科技","https://join.qq.com/","high",
  "UF5SDOR1CY 出自高校就业网正式简章。腾讯岗位可无限投递、随时切换；WXG青云计划同样通用"),
 ("腾讯音乐","DS8DMTYZ / DS0EGNUV","互联网/科技","https://join.tencentmusic.com/campus/","mid",
  "腾讯音乐 HR 体系独立于腾讯集团，两边可各投一次。可选 3 个业务线，提交后不可改"),
 ("字节跳动","BVEUT72 / ZRS2RUF / ZT1X61G / 393YVUG / ISVZV12","互联网/科技",
  "https://jobs.bytedance.com/campus/position?referral_code=BVEUT72","mid",
  "用链接投递自动带码，无需手填。提前批/正式批/实习均通用"),
 ("阿里巴巴","2T51KE6F / 2T4KIB9F / 2T4RBKG3 / 2T4I7977 / 6GJN62T5","互联网/科技","https://talent.alibaba.com/campus","mid",
  "淘天集团与阿里集团口径不同，2T51KE6F 出自淘天内推帖"),
 ("蚂蚁集团","（无需填码）","互联网/科技",
  "https://hrrecommend.antgroup.com/job-list.html?source=campus_external_recommend","high",
  "走带 code 的内推链接投递即自动计入内推，官网投递同样生效，不必找码"),
 ("美团","5D4H35F / FMME439","互联网/科技","https://campus.meituan.com/","mid","网申页内推码栏填入"),
 ("京东集团","XIWC5M / C94TO / C4OF2","互联网/科技","https://campus.jd.com/home","mid",
  "简历页「是否内推」栏填码；京东物流另见 XIWC0P / C4OF2，安全类岗走 TET 技术方向"),
 ("拼多多","I7uVD7damM / d6hCrTjUqq / 7ZQpACk27E / 5gHvmTZFov","互联网/科技",
  "https://careers.pddglobalhr.com/campus/grad?t=I7uVD7damM","mid",
  "链接 t= 后即内推码，用链接投自动计入。技术岗含安全工程师，网络/运维岗偏少"),
 ("快手","campusgFjqZbPgn / campusEeFqXrT / OlfebKXjv / dVRajCCus","互联网/科技",
  "https://campus.kuaishou.cn/recruit/campus/e/h5/#/campus/jobs?code=campusgFjqZbPgn","mid",
  "campus 前缀为小写，后面大小写敏感，整条复制"),
 ("百度","IZH1JB / ISK63T / IZ113R","互联网/科技","https://talent.baidu.com/jobs/campus","mid","网申页推荐码栏"),
 ("滴滴","DSpcu878 / DSkzF6Ts","互联网/科技","https://talent.didiglobal.com/campus","mid","推荐码输入框直接粘贴"),
 ("哔哩哔哩","EC16T7 / 3BCL81 / C2P32W / H490ZN","互联网/科技","https://jobs.bilibili.com/campus/positions","mid",
  "投递后仍可在初筛前撤回重投补码；技术类含开发/测试/运维方向"),
 ("小红书","2HPF4F8GV90G / 47FIQM0JF0YP / 7ZYM4JHM4PN8","互联网/科技","https://job.xiaohongshu.com/campus","mid","校招官网内推码栏"),
 ("得物","JABXADV / VJCQFZW / N9MNWZW / A7KBHYB / 8H2Z2ZZ","互联网/科技","https://www.dewu.com/campus","mid","选岗后找「大使推荐」栏填入"),
 ("微博","NTA1Uv4 / NTAcc9p","互联网/科技","https://app.mokahr.com/social-recruitment/sina/43535?locale=zh-CN#/","low",
  "第 4 位是数字 1 不是小写 l，建议整条复制；2027届技术专场含系统开发/测试开发工程师（测试开发对口你的测试方向）。官网 career.sina.com.cn，网申与内推码在 mokahr 页填写"),
 ("知乎","NTAm131","互联网/科技","https://app.mokahr.com/recommendation-apply/zhihu/3820","low",
  "仅见于聚合平台，官方只在高校宣讲说「找学长学姐内推」，未公布公开码，请先小范围验证"),
 ("携程","NTArwr3 / NTAfGS2 / NTAgLiM / NTA6LY0","互联网/科技","https://campus.ctrip.com/","mid","你已在走 SRE 测评流程，补码可优先筛选"),
 ("唯品会","NTAArwH / NTAAsUz","互联网/科技","https://campus.vip.com/","mid","校招官网推荐码栏"),
 ("金山办公 WPS","DSmB8bjW / NTA79r2","互联网/科技","https://www.wps.cn/","mid","推荐码栏填入"),
 ("顺丰","5CC6RA","互联网/科技","https://campus.sf-express.com/","mid","顺丰科技/顺丰航空通用"),
 ("货拉拉","NTAf566","互联网/科技","https://join.huolala.cn/","mid","推荐码栏"),
 ("途虎养车","DSy4HXDP","互联网/科技","https://www.tuhu.cn/","mid","推荐码栏"),
 ("科大讯飞","EV3RHG / EV3RHJ / IZKMGG / EVBRH0 / ESVCHR","互联网/科技","https://iflytek.zhiye.com/campus/jobs","mid",
  "EV3RHG 源自高校就业网。注意 27 届主要开放的是转正实习岗"),
 ("好未来 / 学而思","DSyKFqbx / DSc7myTe","互联网/科技",
  "https://app.mokahr.com/campus-recruitment/tal/148080?locale=zh-CN","mid","网申时推荐码栏填入"),
 ("小米","4F3HWD7 / QN8KF6Z / XC8BFX8 / 9A4P9J3","互联网/科技","https://xiaomi.jobs.f.mioffice.cn/s/AvRsw8CHbRY","mid",
  "17+ 职类含软件研发/芯片/供应链，投递时选「大使推荐」再填码"),
 ("联想","2027XZLMDWW / lipy19","互联网/科技","https://campus.lenovo.com.cn/","mid",
  "两个版本都流传（2027XXZLMDWW / 2027XZLMDWW），填不上就换；信息来源选「联想员工推荐」后录码"),
 ("智元机器人","XP9JUTE","互联网/科技","https://agirobot.jobs.feishu.cn/s/WIVzPj3j3IE","mid","投递时选「大使推荐」通道再填码"),
 ("浪潮集团","jX7PlGU / 6Bbui47","互联网/科技","https://inspur.hcmcloud.cn/recruit#/campus_category?type=campus","mid",
  "jX7PlGU 首字母小写 j、含数字 7、GU 前是小写 l；6Bbui47 含数字 6 与 47"),
 ("基恩士 KEYENCE","ESVW23 / EVVWB0 / ESVWAG / ES3JR1 / ESVJGG","制造/消费电子","https://www.keyence.com.cn/careers","mid",
  "专业不限全员可投，27 届专属（2026.9–2027.8 毕业）"),
 ("传音控股","EVH89B","制造/消费电子","https://transsion.zhiye.com/campus","mid","深沪渝有岗，支持海外派驻"),
 ("宇通集团","jeycea","制造/消费电子","https://wecruit.hotjob.cn/SU64e7157a1eb80519a8e4efcf/mc/index","mid","先进入管培生通道再填码"),
 ("摩尔线程","IZK6BT","互联网/科技","https://mthreads.zhiye.com/campus","low","GPU 厂商；2027校招含「网络通信与存储」「软件测试/AI测试」，城市含武汉/成都（对口你的网络+测试方向）；官网域名已由 moorethread.com 换为 mthreads.com，旧域名已废弃"),
 # —— 游戏 ——
 ("米哈游","TTTGC / EIXGN / NH5L4 / R92SD / LQFT / 27V7L / 8UEZ","游戏","https://jobs.mihoyo.com/#/campus/position","mid",
  "TTTGC / EIXGN 出自 2027 秋招正式批帖，时效性最好；8UEZ 为老码。应届生仅可投 1 个职位"),
 ("库洛游戏","KTBS4XE / CJ5CGEX / 3CX558C","游戏","https://kurogame.jobs.feishu.cn/campus/","mid","投递时找「大使推荐」栏填码"),
 ("沐瞳科技","HYPRHKD","游戏","https://moonton.jobs.feishu.cn/s/1e3gTUbAygc","mid","推荐方式选「大使推荐」再填码"),
 ("途游游戏","DSQCTCbp / DSry5Z24 / DSncXAVx / DSU41vNb","游戏","https://www.tuyoo.com/campus","mid","推荐码栏"),
 ("巨人网络","DSpXF2Z9 / NTAeCyy","游戏","https://hr.ztgame.com/campus/join/recruit/","mid","推荐码栏"),
 ("三七互娱","DSvAtnc9 / DSeDdRAf / DStcT227","游戏","https://campus.37.com/","mid","推荐码栏"),
 ("莉莉丝","5YDEWZ2 / UWMZ21P","游戏","https://www.lilithgames.com/campus","mid","推荐码栏"),
 ("鹰角网络","NTA9xtN / NTAevja","游戏","https://www.hypergryph.com/","mid","推荐码栏"),
 ("叠纸游戏","A6KRC9P / XVW83QT","游戏","https://www.papegames.com/","mid","推荐码栏"),
 ("网易互娱","TIFh5R / shqAig / XVZ8LnR","游戏","https://game.campus.163.com/","mid","互娱与雷火分开，雷火码 qw4cwo2pomshirr5"),
 ("灵犀互娱","2T4SPDMS / 2T47SF5K","游戏","https://campus.163.com/","mid","推荐码栏"),
 ("深蓝互动","DSrtS5Pm / DSRPdAJN","游戏","https://www.bluepoch.com/","low","聚合帖来源，待验证"),
 # —— 网络安全 / 通信 ——
 ("深信服","NTAWwLF / NTAJG1D / DSJykfXW","网络安全/通信",
  "https://app.mokahr.com/campus_apply/sangfor/27944?recommendCode=DSJykfXW#/jobs","high",
  "NTAWwLF 出自兰州大学就业网正式简章，最稳；NTAJG1D 末尾是数字 1 + D；DSJykfXW 中 y/k/f 为小写"),
 ("亚信安全","V2NRKVF","网络安全/通信","https://asiainfo-sec.jobs.feishu.cn/s/wxf-PC9cvy8","mid",
  "★ 27 届全部岗位免笔试，每人限投 1 个职位。注意是「亚信安全」不是「亚信科技」"),
 ("中兴通讯","NTAXptH / NTAsLJe / NTAgCyp / DSFCrN6z / NTAXcME","网络安全/通信",
  "https://app.mokahr.com/m/campus-recruitment/zte/46903#/home","mid",
  "⚠ 已通过未来领军/实习/中兴捧月投过的，秋招直接官网投，再填内推码会投递失败。四码大小写敏感。武大就业网 9 月简章另给官方内推短链 app.mokahr.com/su/vmqVn"),
 ("华为","（无需内推码）","网络安全/通信","https://career.huawei.com","high",
  "career.huawei.com 是唯一投递入口，官方明确不存在统一校招内推码，任何付费内推都是诈骗。想走员工推荐可把官网生成的简历编号发给对接员工"),
 ("荣耀 HONOR","fvqibr / rgltca / yhshcb / ofsski / aajvef","制造/消费电子",
  "https://career.honor.com/SU60ee9e002f9d247b98da489e/mc/position/campus?acotycoCode=ofsski","mid",
  "27 届 14 类 70+ 岗位，网申时填推荐码。⚠ 本硕简历截止 2026-09-30 24:00，aajvef 出自牛客 27 届官方启动帖，五码任选其一"),
 ("OPPO","X3448036 / Z71213103 / X6538748 / 80417111","制造/消费电子","https://careers.oppo.com/university/oppo/campus/post","high",
  "X3448036 出自华中农业大学就业网官方简章，最稳妥；每人最多 2 个志愿"),
 ("大疆 DJI","DSGz7tGD / DSvFhRaB / DSKeRdhz","互联网/科技",
  "https://app.mokahr.com/m/campus_apply/dji/143359?recommendCode=DSGz7tGD#/jobs","high",
  "DSGz7tGD 来自温州大学/中国矿大(北京)就业网正式简章。★ 27 届「拓疆者」含信息安全岗；每人限投 1 个职位且投递后无法更改"),
 # —— 制造 / 半导体 / 汽车 ——
 ("宁德时代","DS8Msaj4 / DSWb7qYg / DS85hmhK / DSgVdcN4","制造/半导体/汽车",
  "https://app.mokahr.com/m/campus-recruitment/catlhr/148948?recommendCode=DS8Msaj4#/jobs","mid",
  "6 大职类含「计算机与 AI 类」（适配计算机/信息通信）；每人仅 3 次投递机会，DS 前缀后大小写敏感"),
 ("蔚来 NIO","R6D4SHC / BSB3WU7 / ZR99UBS / 7MRKZ2D","制造/半导体/汽车","https://nio.jobs.feishu.cn/s/iPgS2LfV","mid",
  "★ 岗位大类含「数字技术类（平台规划、开发与运维）」，与你方向对口；渠道选「大使推荐」。投递前别自己先网申，否则无法转内推"),
 ("理想汽车","H56UNDK / NTAHDru","制造/半导体/汽车","https://www.lixiang.com/employ/campus/list.html?employchannelcode=H56UNDK&job_mode=1","mid",
  "H56UNDK 是官方公告里的合作渠道码（非员工个人码），见于多所高校就业网转载链接"),
 ("小鹏汽车","GWVHCUY / CK45VF3","制造/半导体/汽车","https://xiaopeng.jobs.feishu.cn/s/pHOutLy9DZ4","mid","CK45VF3 为校园大使推荐码"),
 ("吉利控股","DSPW7fqP / DSV9DCmy / DSpTqw8Y","制造/半导体/汽车",
  "https://app.mokahr.com/campus_apply/geely/78436?recommendCode=DSPW7fqP#/jobs","mid",
  "★ 九大方向明确含「IT/互联网类」；每人限投 3 岗。DSPW7fqP 与 DSpTqw8Y 仅第 3–5 位大小写不同，务必整条复制"),
 ("寒武纪","NTAr8IQ / NTAtrFW / NTAsz7D","制造/半导体/汽车","https://app.mokahr.com/su/iapaps","mid",
  "★ 西安交大就业网简章需求专业含「网络空间安全 / 网络与信息安全」；填网申「推荐码」栏，发布者可查进度"),
 ("地平线","lhybtw / khpwgf / ryhrdn / Iszvkn","制造/半导体/汽车",
  "https://wecruit.hotjob.cn/SU62d915040dcad43c775ec12c/mc/position/campus?acotycoCode=lhybtw&projectId=103302&recruitType=1","mid",
  "lhybtw 首字符是小写 L，Iszvkn 首字符是大写 i，极易混"),
 ("京东方 BOE","FY34V","制造/半导体/汽车","http://campus.boe.com/","mid",
  "★ 岗位列表明确含「信息安全专员」；也可走「BOE 校园招聘内部推荐」小程序让学长学姐生成专属码"),
 ("紫光展锐","12785","制造/半导体/汽车","https://www.unisoc.com/campus","low",
  "填的是员工工号不是字母码，官方未公开字母内推码，有效性需自行核验"),
 ("中芯国际","BJ06 / BJ01","制造/半导体/汽车","https://www.smics.com/","low","聚合帖口径，待验证"),
 ("汇川技术","ABBPREB / AKKFRT8 / RE8SMYZ","制造/半导体/汽车","https://inovance.zhiye.com/campus","mid","推荐码栏"),
 ("欣旺达","EVVS3B / EVBXT3 / ESKZ3H","制造/半导体/汽车","https://www.sunwoda.com/","mid","动力电池方向另见 EVKSSJ"),
 ("正浩创新 EcoFlow","GNU4GHP","制造/消费电子","https://jobs.ecoflow.com/602892","mid","★ 你已投两次 SRE 岗，网申 9 月底关，投之前先补码"),
 ("阳光电源","NTAuMBe / NTAwHpR / NTAuBxF","制造/半导体/汽车","https://jobs.sungrowpower.com/","mid","推荐码栏"),
 ("远景能源","DSYMXZk1 / NTAMT0m / DSC64ted / DSK3HYpH","制造/半导体/汽车","https://envision-career.com","mid","推荐码栏"),
 ("金风科技","ISKP8G / IVVP80","制造/半导体/汽车","https://www.goldwind.com/","mid","推荐码栏"),
 ("三一集团","ESKMBS / ESKM1A / EVKM80 / EVKM9J","制造/半导体/汽车","https://sany.zhiye.com/campus","mid","推荐码栏"),
 ("豪迈集团","EVHPGS","制造/半导体/汽车","https://www.himile.com/","mid","推荐码栏"),
 ("华勤技术","NTArpLU / NTAjpG8","制造/消费电子","https://campus.huaqin.com/","mid","推荐码栏"),
 ("九号公司","NTAvBkk","制造/消费电子","https://www.ninebot.com/","mid","推荐码栏"),
 ("奥克斯","ESVM8G","制造/消费电子","https://www.auxgroup.com/","mid","推荐码栏"),
 ("春风动力","ESVYR1","制造/消费电子","https://www.cfmoto.com/","mid","推荐码栏"),
 # —— 消费电子 / 家电 ——
 ("海尔","GHJ493 / GHJ491 / GHJ498 / GHJ462 / GHJ551","制造/消费电子",
  "https://maker.haier.net/client/campusmobile/customizedjobs/type/top.html","mid",
  "填法特殊：招聘信息来源选「未来规划局推荐」再填码。GHJ493 与 GHJ491 仅末位不同"),
 ("海信","ES1PTH / EV1PVR","制造/消费电子","https://jobs.hisense.com/","mid","推荐码栏"),
 ("TCL实业","ytgwuf / awfvzp","制造/消费电子",
  "https://actyco.wintalent.cn/actyco/home/receiver/poster/redirect?id=2ce781f69fb84c0101a0330197af22af","mid",
  "★ 职能类含「IT 与数字化类」；ytgwuf 末位是 f 不是 t"),
 ("TCL华星光电","tyfqth / vkjzoi / kjrbup","制造/消费电子",
  "https://actyco.wintalent.cn/actyco/home/receiver/poster/redirect?id=2ce781f69fb84c0101a0330197af22af","mid",
  "与 TCL 实业同一系统，两子公司合计限投 2 岗；tyfqth / vkjzoi 为校园大使码"),
 ("美的集团","M4I451 / MZ6426 / M1582V / MJ2655 / M4Y642 / M772H4","制造/消费电子",
  "https://careers.midea.com/recruit-school-wechat/job?mvp_code=M4I451&type=1","high",
  "M4I451 出自多所高校就业网公告；M772H4 出自华中师范大学就业网 27 届简章（校园大使码）。★ 八大职类含「信息技术类」；填法为「应聘信息获取渠道」选「伯乐推荐」再填码，已投递可在个人中心补填"),
 ("格力电器","CGREE77820 / BGREE36819 / CGREE15965 / BGREE99853","制造/消费电子","https://zhaopin.greeyun.com/home","high",
  "CGREE77820 出现在华中师大/重庆大学等多校就业网公告，可信度最高。★ 信息技术类明确含「信息安全」岗"),
 ("立讯精密","thnicf","制造/消费电子","https://luxshare.hotjob.cn","low",
  "★ 明确设「IT 岗（网络/数据库管理/资讯安全工程师）」，专业含网络工程。官方只说向星光大使索取个人码，thnicf 为聚合帖口径待验证"),
 # —— 金融 ——
 ("招商银行","QWGIRT / UDDRZL / MWLWTF / ISMWTH","金融/银行","https://career.cmbchina.com/","mid",
  "总行/分行由行员在「招商银行招聘」公众号→招了→YOU伯乐→校招内推生成专属码；招银网络科技口径 QWGIRT"),
 ("宁波银行","（需向员工索取）","金融/银行","https://zhaopin.nbcb.com.cn/","high",
  "★ 有总行金融科技定向生（应用研发、运维 SRE、安全技术、运行操作），截止 10-31。无公开码，需找在职员工/校园大使要个人专属码"),
 ("度小满","K6KVY14","金融/银行","https://campus.duxiaoman.com/","mid","推荐码栏"),
]

# ---------- 确认无需内推码 / 无内推机制 ----------
# (公司, 分类, 说明, 官方投递入口)
NOREF = [
 ("蚂蚁集团","互联网/科技","走带 code 的内推链接或官网投递即自动计入内推，不必找码","https://hrrecommend.antgroup.com/job-list.html?source=campus_external_recommend"),
 ("华为","网络安全/通信","career.huawei.com 唯一入口，官方明确无统一校招内推码；凡收费内推均为诈骗","https://career.huawei.com"),
 ("长江存储","制造/半导体/汽车","内推填的是「推荐人工号」而非公开码，需向在职员工索取；网申 08-27~10-26，最多投 3 个职位","https://ymtc.zhiye.com"),
 ("中国农业银行","金融/银行","公告原文「我行招聘为公开招聘，无任何形式的内推」","https://career.abchina.com.cn/"),
 ("交通银行","金融/银行","无内推机制，仅官网及官方公众号投递；金融科技岗含安全技术、数据安全","https://job.bankcomm.com/"),
 ("兴业银行","金融/银行","无内推机制；科技专项人才含运维方向，截止 10-25","https://job.cib.com.cn/"),
 ("浦发银行","金融/银行","无内推机制；科技储备生含信息安全、系统及网络运维，截止 10-08 18:00","https://job.spdb.com.cn/"),
 ("中国民生银行","金融/银行","无内推机制；科技/STEM 类岗位，截止 10-25","https://career.cmbc.com.cn/"),
 ("中信银行(总行)","金融/银行","官方声明统一通过官网投递，无其他报名渠道；信息科技类岗，截止 10-09","https://job.citicbank.com/"),
 ("杭州银行","金融/银行","无内推机制；总行信息技术部培训生，截止 10-25","https://myjob.hzbank.com.cn/"),
 ("中国邮政储蓄银行","金融/银行","无内推机制；总行金融科技岗、中邮消费金融信息安全岗，截止 10-07","https://psbc2027.zhaopin.com/"),
 ("中国光大银行","金融/银行","无内推机制；金融科技岗、安全管理岗（北京），网申约 09-28~11-09","http://cebbank.51job.com/"),
 ("中国移动","网络安全/通信","无内推码机制，官方警示凡收费「内推」均为诈骗；10-24 集团统一笔试，最多 2 个志愿","https://job.10086.cn"),
 ("中国联通","网络安全/通信","无内推码机制，官网/智联/国聘三平台选其一投递，重复投递影响筛选；笔试 11 月上旬","https://zglt.zhaopin.com"),
 ("中国铁塔","网络安全/通信","官网 zhaopin.chinatowercom.cn 是唯一报名入口，无内推码，警惕「保录取」收费；9/26 查证 27 届正式批公告尚未发布，往年 10 月中旬网申","https://zhaopin.chinatowercom.cn/"),
 ("中邮消费金融","金融/银行","未检索到公开内推码；走飞书网申或公众号【中邮消费金融招聘】投递。IT技术类含信息安全岗（广州），高校就业网帖子有效期至 10-07","https://is35svcbne.jobs.feishu.cn/youcash/"),
 ("中国银联","金融/银行","官网注册后「立即申请该职位」，未见 27 届公开内推码","https://join.unionpay.com/"),
 ("国家电网","金融/运营商/电网","无内推机制；电子信息类含计算机与网络与信息安全，国网信通提前批约 10 月底截止","https://zhaopin.sgcc.com.cn/"),
 ("南方电网","金融/运营商/电网","无内推机制；提前批有信息通信业务岗（数字电网开发、网络安全）","https://zhaopin.csg.cn/"),
 ("中广核","金融/运营商/电网","无内推机制；计算机类/电子信息类（数字科技方向），09-04 起开放","https://www.cgnpc.com.cn/"),
 ("中国电子科技集团 CETC","国企/央企","无内推机制；电科网安、三十所等有网络安全类岗位，校招入口见公告二维码","https://www.cetc.com.cn/"),
 ("奇安信","网络安全/通信","官方明确需联系员工或校园大使获取内推码，无全网通用公开码；网申截止 11-14，每人 2 个志愿","https://campus.qianxin.com/"),
 ("安恒信息","网络安全/通信","无公开码，搜到的 AH8837 为 2022 年前后旧帖；27 届含安全服务、渗透测试岗，官网或公众号投递","https://www.dbappsecurity.com.cn/"),
 ("启明星辰","网络安全/通信","无公开码，官网未设推荐码入口；27 届岗 9 月中旬上线，网申与内推并行至 2027-06-30","https://venustech2.zhiye.com/campus/jobs"),
 ("天融信","网络安全/通信","无公开码，旧码 ESVMKA / EVKMT9 为 22 届；投递走官网或「天融信招聘」公众号","https://www.topsec.com.cn/hr/campus.html"),
 ("山石网科","网络安全/通信","官方只说向在职员工要码，旧码 ISVMAK / IVKM9G 为 24-25 届不适用","https://hillstonenet.zhiye.com/campus"),
 ("长亭科技","网络安全/通信","无公开码，旧码 NTAWkpg 为 25 届；招聘官网 join.chaitin.cn（原 mokahr 链接已关停）或简历直投 resume@chaitin.com","https://join.chaitin.cn/"),
 ("三六零 360","网络安全/通信","系统有推荐码栏但需向员工索取；牛客可见 IS3YH9 / EVBAGS 等均为 26 届及更早旧码。第一批笔试 10-10","https://360campus.zhiye.com/campus/jobs"),
 ("美亚柏科","网络安全/通信","仅有「内部推荐」（上传简历、无码）通道；投递走 www.300188.cn 或公众号","https://hr.300188.cn/"),
 ("赛力斯","制造/半导体/汽车","官方仅写「找学长学姐获取内推链接」，未放出可核验的公开码；职能类含 IT 岗","https://auto.seres.cn/recruitIndex"),
 ("长安汽车","制造/半导体/汽车","未见公开内推码，只走官网与公众号；设数字化技术类/智能网联研发类","http://changan.zhiye.com/Campus"),
 ("上汽集团","制造/半导体/汽车","未见公开内推码，仅 PC 端官网 + 公众号投递；岗位含信息系统方向","https://saic-recruit.saicmotor.com"),
 ("广汽集团","制造/半导体/汽车","未见公开内推码，仅官网网申；岗位含智能网联/数字化类","https://xyzp.51job.com/gacgroup2027"),
  ("比亚迪","制造/半导体/汽车","2027 届官方未放公开码，BYDNTA04/05 为 26 届春招旧码；硕士岗列网络与信息安全","https://job.byd.com/portal/pc"),
]

# 待办的「备用入口」：主链接失效 / 要确认参加 / 要找练习入口时用得上
# key = TODOS 里的公司名，value = [(按钮文字, URL), ...]
TODO_EXTRA = {
    "京东集团": [
        ("确认是否参加", "https://hr.nowcoder.com/v1/s/DLZbaDPw#"),
        ("技术岗练习入口", "https://exam.nowcoder.com/cts/17522284/summary"),
        ("校招官网", "https://campus.jd.com"),
    ],
    "携程集团": [
        ("确认参加", "https://app.mokahr.com/exam-status?attendStatus=accepted&access_token=fbf5d03417dd48a3a609879ebcb321a28b1f3547ea0f4a4aabde1a16e6cab214"),
        ("谢绝", "https://app.mokahr.com/exam/reject-reason-page?access_token=fbf5d03417dd48a3a609879ebcb321a28b1f3547ea0f4a4aabde1a16e6cab214"),
    ],
    "深圳市卓驭科技": [("备用作答入口", "https://bsurl.cn/v2/rSN9Wdo9")],
    "新华三技术": [
        ("备用作答入口", "https://bsurl.cn/v2/hTffEOp8"),
        ("校招官网", "https://career.h3c.com/"),
    ],
    "汇川技术": [("招聘官网", "https://recruit.inovance.com")],
    "米哈游 miHoYo": [("校招官网", "https://jobs.mihoyo.com")],
}

# ---------- 组装 ----------
def dl_state(dl):
    if not dl:
        return "none", "未公布 / 招满即止"
    y, m, d = [int(x) for x in dl.split("-")]
    n = (datetime.date(y, m, d) - TODAY).days
    if n < 0:  return "over", f"{dl}（已截止）"
    if n <= 7: return "hot",  f"{dl}（剩 {n} 天）"
    if n <= 14: return "warn", f"{dl}（剩 {n} 天）"
    return "ok", f"{dl}（剩 {n} 天）"

todos = []
for t in TODOS:
    typ, comp, item, dl, url, note = t
    dt = datetime.datetime.strptime(dl, "%Y-%m-%d %H:%M")
    todos.append({"type": typ, "comp": comp, "item": item, "dl": dl,
                  "iso": dt.strftime("%Y-%m-%dT%H:%M:%S"), "url": url, "note": note,
                  "extra": [{"label": lb, "url": u} for lb, u in TODO_EXTRA.get(comp, [])]})
todos.sort(key=lambda x: x["iso"])

pending = [{"type": p[0], "comp": p[1], "item": p[2], "url": p[3]} for p in PENDING]
dead = [{"cat": d[0], "comp": d[1], "item": d[2], "time": d[3], "note": d[4]} for d in DEAD]

mine = []
for d in bcs.DATA:
    st, txt = dl_state(d[8])
    mine.append({"seq": d[0], "name": d[1], "role": d[2], "loc": d[3], "status": d[4],
                 "cat": d[5], "url": d[6], "note": d[7], "urg": st, "dlTxt": txt,
                 "raw": d[8], "sort": (datetime.date(*[int(x) for x in d[8].split("-")]) - TODAY).days if d[8] else 9999})

# ---------- 去重：已投递的公司不出现在「可补投通道」 ----------
# 看起来像但其实不是同一家，永不判重复
NOT_SAME = [
    ("京东", "京东方"), ("京东", "京东物流"),
    ("腾讯", "腾讯音乐"), ("腾讯", "腾讯健康"),
    ("阿里", "阿里健康"), ("中国通号", "通号"),
    ("中国电信", "中国移动"), ("中国电信", "中国联通"),
    ("招商银行", "招银网络科技"), ("中国工商银行", "中国建设银行"),
    ("中国工商银行", "中国农业银行"), ("中国工商银行", "交通银行"),
    ("中国工商银行", "中国邮政储蓄银行"), ("中国工商银行", "中信银行"),
    ("中国工商银行", "浦发银行"), ("中国工商银行", "兴业银行"),
    ("中国工商银行", "中国民生银行"),
    ("东风汽车", "长安汽车"), ("东风汽车", "上汽集团"),
    ("东风汽车", "广汽集团"), ("东风汽车", "吉利控股"),
    ("东风汽车", "小鹏汽车"), ("东风汽车", "理想汽车"),
    ("东风汽车", "蔚来"), ("东风汽车", "比亚迪"),
    ("通号工程局集团", "通号工程电气化局"), ("通号工程局集团", "通号低空"),
    ("通号工程电气化局", "通号低空"), ("通号低空", "北京现代通号工程咨询"),
]
# 明确是同一家的不同写法（台账名 vs 通道名）
ALIAS = [
    ("中国移动湖北公司", "中国移动"), ("湖北移动", "中国移动"),
    ("中国电信", "中国电信"), ("千问（阿里巴巴）", "阿里巴巴"),
    ("智元机器人（AGIBOT）", "智元机器人"), ("网易（互娱）", "网易"),
    ("湖北亿纬动力（亿纬锂能）", "亿纬锂能"), ("亿纬锂能（社招）", "亿纬锂能"),
    # 台账里带英文缩写后缀，会被 NOT_SAME("腾讯","腾讯音乐") 的子串规则误杀，显式配对
    ("腾讯音乐 TME", "腾讯音乐"), ("腾讯音乐TME", "腾讯音乐"),
]


# 知名两字简称：作为长名的前缀出现时判为同一家（配合上面的 NOT_SAME 表防误伤）
SHORT_OK = ["小米", "海尔", "美的", "格力", "华为", "中兴", "联想", "大疆", "蔚来", "吉利",
            "百度", "美团", "腾讯", "网易", "字节", "京东", "顺丰", "海信", "长虹", "比亚迪",
            "宁德", "三一", "浪潮", "金蝶", "长城", "长安", "广汽", "上汽", "东风", "奇瑞",
            "海康", "大华", "oppo", "vivo", "携程", "滴滴", "快手", "微博", "知乎", "拼多多",
            "荣耀", "哔哩哔哩"]


def _norm(s):
    for ch in " （）()·-/&":
        s = s.replace(ch, "")
    return s.lower()


def is_same(a, b):
    """判断两个公司名是否指同一家"""
    na, nb = _norm(a), _norm(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    for x, y in ALIAS:
        nx, ny = _norm(x), _norm(y)
        if (na == nx and nb == ny) or (na == ny and nb == nx):
            return True
    for x, y in NOT_SAME:
        nx, ny = _norm(x), _norm(y)
        if (nx in na or nx in nb) and (ny in na or ny in nb):
            return False
    short, long = (na, nb) if len(na) <= len(nb) else (nb, na)
    if len(short) >= 3 and short in long:
        return True
    # 前 4 字相同且双方都不短（如「中国移动（集团）」vs「中国移动湖北公司」）
    if len(na) >= 4 and len(nb) >= 4 and na[:4] == nb[:4]:
        return True
    # 知名两字简称 + 前缀（如「小米」vs「小米集团」）
    if short in SHORT_OK and long.startswith(short):
        return True
    return False


_ledger_names = [d[1] for d in bcs.DATA]

# 手动标记的「已投」公司：从同目录的 手动已投标记.txt 读取（每行一个公司名，# 开头为注释）
# 这个文件是手动标记的持久化来源 —— 浏览器 localStorage 清缓存会丢，写进这个文件才长期生效
MANUAL_FILE = os.path.join(OUT_DIR, "手动已投标记.txt")
_manual_names = []
if os.path.exists(MANUAL_FILE):
    with open(MANUAL_FILE, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s and not s.startswith("#"):
                _manual_names.append(s)
else:
    with open(MANUAL_FILE, "w", encoding="utf-8") as f:
        f.write("# 手动标记为「已投」的公司，每行一个，会被自动从「可补投通道」剔除\n"
                "# 写法：直接写公司名即可，可用台账里的简称；# 开头为注释\n"
                "# 例：\n"
                "# 蔚来\n"
                "# 亚信安全\n")

# 全部「已投」依据 = 台账 + 手动名单
_applied_all = _ledger_names + _manual_names

_moved = []
_new_kept = []
for _n in NEW:
    _hit = None
    for _m in _ledger_names:
        if is_same(_n[0], _m):
            _hit = _m
            break
    if _hit:
        _moved.append({"name": _n[0], "ledger": _hit, "cat": _n[1], "src": "台账"})
    else:
        _manual_hit = None
        for _m in _manual_names:
            if is_same(_n[0], _m):
                _manual_hit = _m
                break
        if _manual_hit:
            _moved.append({"name": _n[0], "ledger": _manual_hit, "cat": _n[1], "src": "手动标记"})
        else:
            _new_kept.append(_n)

newch = []
for n in _new_kept:
    st, txt = dl_state(n[4])
    newch.append({"name": n[0], "cat": n[1], "fit": n[2], "url": n[3], "note": n[5],
                  "urg": st, "dlTxt": txt, "raw": n[4],
                  "sort": (datetime.date(*[int(x) for x in n[4].split("-")]) - TODAY).days if n[4] else 9999})
newch.sort(key=lambda x: (x["sort"], x["name"]))

uncf = [{"name": u[0], "cat": u[1], "note": u[2]} for u in UNCONFIRMED]

refs = []
for r in REF:
    codes = [c.strip() for c in r[1].split("/") if c.strip()]
    if codes and codes[0].startswith("（"):   # 「（无需填码）」「（需向员工索取）」这种不是真码
        codes = []
    refs.append({"name": r[0], "codes": codes, "raw": r[1], "cat": r[2], "url": r[3],
                 "src": r[4], "note": r[5],
                 "mine": any(is_same(r[0], m) for m in _applied_all)})
refs.sort(key=lambda x: (not x["mine"], x["cat"], x["name"]))

noref = [{"name": n[0], "cat": n[1], "note": n[2], "url": n[3]} for n in NOREF]
noref.sort(key=lambda x: (x["cat"], x["name"]))

html = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>姜艺 · 秋招工作台</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#f4f5f7;color:#1f2329;padding:20px}
  .wrap{max-width:1360px;margin:0 auto}
  header{background:linear-gradient(135deg,#fff 0%,#f8faff 100%);border:1px solid #e5e6eb;border-radius:14px;padding:22px 26px;margin-bottom:16px}
  h1{font-size:22px;font-weight:600;margin-bottom:4px}
  .sub{font-size:12.5px;color:#86909c;line-height:1.7}
  .stats{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}
  .stat{flex:1;min-width:120px;background:#fff;border:1px solid #e5e6eb;border-radius:10px;padding:12px 14px}
  .stat b{display:block;font-size:23px;font-weight:600;line-height:1.2}
  .stat span{font-size:11.5px;color:#86909c}
  nav{display:flex;gap:6px;margin-bottom:14px;flex-wrap:wrap}
  .tab{padding:10px 20px;border:1px solid #e5e6eb;background:#fff;border-radius:9px;font-size:14px;cursor:pointer;user-select:none}
  .tab.on{background:#3b6ef5;color:#fff;border-color:#3b6ef5;font-weight:500}
  .tab i{font-style:normal;opacity:.75;font-size:12px;margin-left:5px}
  .toolbar{background:#fff;border:1px solid #e5e6eb;border-radius:11px;padding:12px 16px;margin-bottom:14px;display:flex;gap:9px;flex-wrap:wrap;align-items:center}
  input[type=text]{flex:1;min-width:180px;padding:9px 13px;border:1px solid #d9dce0;border-radius:8px;font-size:13.5px;outline:none}
  input[type=text]:focus{border-color:#3b6ef5}
  .chip{padding:6px 13px;border:1px solid #d9dce0;border-radius:18px;font-size:12.5px;cursor:pointer;background:#fff;user-select:none}
  .chip.on{background:#3b6ef5;color:#fff;border-color:#3b6ef5}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:13px}
  .card{background:#fff;border:1px solid #e5e6eb;border-radius:12px;padding:15px 17px;display:flex;flex-direction:column;gap:7px;border-left:4px solid #c9cdd4}
  .card.hot{border-left-color:#e54545;background:#fffafa}
  .card.warn{border-left-color:#ff9a2e}
  .card.over{border-left-color:#c9cdd4;opacity:.75}
  .card.ok{border-left-color:#23a55a}
  .card h3{font-size:15px;font-weight:600;display:flex;align-items:center;gap:7px;flex-wrap:wrap}
  .tag{font-size:11px;padding:2px 7px;border-radius:4px;font-weight:400;background:#f2f3f5;color:#86909c}
  .tag.hi{background:#e8f7ee;color:#1a8a4a}
  .tag.type{background:#eef3ff;color:#3b6ef5}
  .role{font-size:12.8px;color:#4e5969;line-height:1.55}
  .meta{font-size:11.8px;color:#86909c;display:flex;gap:10px;flex-wrap:wrap}
  .note{font-size:11.8px;color:#4e5969;background:#f7f8fa;border-radius:6px;padding:7px 10px;line-height:1.6}
  .cd{font-size:12.5px;font-weight:600;padding:4px 9px;border-radius:6px;display:inline-block;font-variant-numeric:tabular-nums}
  .cd.hot{background:#ffece8;color:#e54545}
  .cd.warn{background:#fff7e8;color:#d97706}
  .cd.ok{background:#e8f7ee;color:#1a8a4a}
  .cd.over{background:#f2f3f5;color:#a9aeb8}
  .cd.none{background:#f2f3f5;color:#86909c}
  a.btn{display:block;text-align:center;padding:8px;background:#3b6ef5;color:#fff;border-radius:8px;text-decoration:none;font-size:13px;font-weight:500}
  a.btn:hover{background:#2f5ccc}
  a.btn.g{background:#f2f3f5;color:#4e5969;margin-top:5px}
  a.btn.g:hover{background:#e5e6eb}
  a.btn.na{background:#f2f3f5;color:#a9aeb8;pointer-events:none}
  .btns{display:flex;gap:6px}
  .btns a{flex:1}
  .exlinks{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px;padding-top:8px;border-top:1px dashed #e5e6eb}
  .exlinks a{font-size:11.5px;color:#4e5969;text-decoration:none;background:#f7f8fa;border:1px solid #e5e6eb;border-radius:6px;padding:3px 8px}
  .exlinks a:hover{background:#eef3ff;border-color:#b6cbff;color:#3b6ef5}
  h2.sec{font-size:15px;font-weight:600;margin:22px 0 11px;padding-left:9px;border-left:4px solid #3b6ef5}
  h2.sec.g{border-left-color:#86909c}
  .empty{padding:36px;text-align:center;color:#86909c;font-size:13.5px}
  table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e5e6eb;border-radius:10px;overflow:hidden;font-size:13px}
  th{background:#f7f8fa;text-align:left;padding:10px 13px;font-weight:600;color:#4e5969;font-size:12.5px}
  td{padding:9px 13px;border-top:1px solid #f0f1f3;vertical-align:top}
  td.c{color:#86909c;font-size:12.5px}
  .pill{display:inline-block;padding:2px 8px;border-radius:11px;font-size:11.5px}
  .pill.a{background:#ffece8;color:#e54545}
  .pill.b{background:#e8f7ee;color:#1a8a4a}
  .pill.c{background:#f2f3f5;color:#86909c}
  .pill.d{background:#fff7e8;color:#d97706}
  .code{font-family:"SF Mono",Consolas,Monaco,monospace;font-size:14px;font-weight:600;letter-spacing:.5px;
        background:#eef3ff;color:#2f5ccc;border:1px dashed #b9cbff;border-radius:7px;padding:7px 11px;display:inline-block;
        cursor:pointer;user-select:all;margin:2px 3px 2px 0;transition:.15s}
  .code:hover{background:#2f5ccc;color:#fff;border-style:solid}
  .code.na{background:#f2f3f5;color:#a9aeb8;border-color:#e5e6eb;cursor:default}
  .code.na:hover{background:#f2f3f5;color:#a9aeb8}
  .codebar{display:flex;flex-wrap:wrap;gap:2px;align-items:center}
  .src{font-size:10.5px;padding:1px 6px;border-radius:4px;font-weight:500}
  .src.high{background:#e8f7ee;color:#1a8a4a}
  .src.mid{background:#eef3ff;color:#3b6ef5}
  .src.low{background:#fff7e8;color:#d97706}
  .mine{font-size:10.5px;padding:1px 6px;border-radius:4px;background:#f2f3f5;color:#86909c}
  .mine.y{background:#ffece8;color:#e54545}
  #toast{position:fixed;left:50%;bottom:34px;transform:translateX(-50%) translateY(14px);background:#1f2329;color:#fff;
         padding:10px 20px;border-radius:9px;font-size:13px;opacity:0;pointer-events:none;transition:.22s;z-index:99}
  #toast.on{opacity:1;transform:translateX(-50%) translateY(0)}
  footer{margin-top:24px;font-size:11.5px;color:#a9aeb8;text-align:center;line-height:1.8}
  .hide{display:none}
  /* 内置浏览器浮层：在阿禾内独立显示官网，可关闭返回工作台 */
  /* 右侧抽屉：工作台始终留在左侧可见，同一阿禾标签内同屏显示，关闭即返回工作台 */
  #frameLayer{position:fixed;top:0;right:0;height:100%;width:72%;max-width:1080px;background:#fff;z-index:9999;display:flex;flex-direction:column;box-shadow:-6px 0 22px rgba(0,0,0,.18);border-left:1px solid #e4e7ec}
  @media (max-width:760px){#frameLayer{width:100%}}
  #frameLayer.hide{display:none}
  .fl-bar{display:flex;align-items:center;gap:8px;padding:8px 12px;background:#1f2329;color:#fff;flex:0 0 auto}
  .fl-bar .fl-title{font-weight:600;font-size:13px;max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .fl-url{flex:1;background:#fff;color:#1f2329;border:none;border-radius:6px;padding:6px 9px;font-size:12px;min-width:0}
  .fl-bar button{background:#3b6ef5;color:#fff;border:none;border-radius:6px;padding:6px 11px;font-size:12px;cursor:pointer;white-space:nowrap}
  .fl-bar button.ghost{background:#3a3f47}
  .fl-bar button.close{background:#e54545}
  .fl-warn{display:none;background:#fff7e8;color:#d97706;border-bottom:1px solid #ffd591;padding:8px 12px;font-size:12.5px;flex:0 0 auto;line-height:1.6}
  .fl-warn.show{display:block}
  #frameFrame{flex:1;border:none;width:100%;background:#fff}
  </style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>姜艺 · 秋招工作台</h1>
    <div class="sub">
      整合：<b>邮件追踪待办</b>（测评/笔试/面试/投递）· <b>已投递公司校招官网</b>（台账 __N_MINE__ 家）· <b>可补投大厂通道</b>（__N_NEW__ 家）· <b>内推码</b>（__N_REF__ 家，另有 __N_NOREF__ 家确认无需内推码）<br>
      校招官网与内推码均于 2026-09-26 联网核实　|　数据源：QQ邮箱 + WPS云盘《工作计划完成统计表1.xlsx》「五月」sheet + 高校就业网/牛客　|　最后更新：<b>2026-09-26</b>
    </div>
    <div class="stats">
      <div class="stat"><b style="color:#e54545" id="stat-todo">__N_TODO__</b><span>进行中待办</span></div>
      <div class="stat"><b>__N_MINE__</b><span>已投递公司</span></div>
      <div class="stat"><b style="color:#1a8a4a" id="stat-new">__N_NEW__</b><span>可补投通道</span></div>
      <div class="stat"><b style="color:#d97706">__N_REF__</b><span>内推码</span></div>
      <div class="stat"><b style="color:#86909c">__N_DEAD__</b><span>已结束/未通过</span></div>
      <div class="stat"><b style="color:#d97706">__N_HOT__</b><span>7天内截止</span></div>
    </div>
  </header>

  <nav>
    <span class="tab on" data-t="todo">🔥 待办<i id="tab-todo-n">__N_TODO__</i></span>
    <span class="tab" data-t="mine">📮 我的投递<i>__N_MINE__</i></span>
    <span class="tab" data-t="new">🚀 可补投通道<i id="tab-new-n">__N_NEW__</i></span>
    <span class="tab" data-t="ref">🎟 内推码<i>__N_REF__</i></span>
    <span class="tab" data-t="dead">🗂 已结束 / 未通过<i>__N_DEAD__</i></span>
  </nav>

  <div id="pane-todo">
    <div class="toolbar">
      <input type="text" id="q1" placeholder="搜索公司 / 事项…">
      <span class="chip on" data-f="all">全部</span>
      <span class="chip" data-f="hot">7天内</span>
      <span class="chip" data-f="笔试">笔试</span>
      <span class="chip" data-f="测评">测评</span>
      <span class="chip" data-f="投递">投递</span>
      <span class="chip" data-f="简历">简历</span>
      <span class="chip" data-f="活动">活动</span>
    </div>
    <div class="grid" id="g-todo"></div>
    <h2 class="sec g">另有 __N_PEND__ 项无明确截止，尽快处理</h2>
    <div class="grid" id="g-pend"></div>
    <div id="done-bar" class="hide" style="margin-top:13px;font-size:12.5px;color:#4e5969;background:#fff;border:1px solid #e5e6eb;border-radius:10px;padding:11px 15px">
      你已处理 <b id="done-n">0</b> 项，已从上方划掉。
      <a href="javascript:void(0)" id="done-show" style="color:#3b6ef5;text-decoration:none;margin-left:8px">显示已处理</a>
      <a href="javascript:void(0)" id="done-undo" style="color:#3b6ef5;text-decoration:none;margin-left:8px">恢复全部</a>
      <div style="margin-top:6px;color:#a9aeb8">标记存在本机浏览器，换设备不同步；每天脚本重生成后仍在（除非清缓存）。</div>
    </div>
  </div>

  <div id="pane-mine" class="hide">
    <div class="toolbar">
      <input type="text" id="q2" placeholder="搜索公司 / 岗位 / 地点…">
      <span class="chip on" data-f="all">全部</span>
      <span class="chip" data-f="hot">7天内截止</span>
      <span class="chip" data-f="互联网/科技">互联网/科技</span>
      <span class="chip" data-f="游戏">游戏</span>
      <span class="chip" data-f="网络安全/通信">网络安全/通信</span>
      <span class="chip" data-f="国企/金融/能源">国企/金融/能源</span>
      <span class="chip" data-f="制造/消费电子">制造/消费电子</span>
      <span class="chip" data-f="待核对">待核对</span>
    </div>
    <div class="grid" id="g-mine"></div>
  </div>

  <div id="pane-new" class="hide">
    <div class="toolbar">
      <input type="text" id="q3" placeholder="搜索公司 / 备注…">
      <span class="chip on" data-f="all">全部</span>
      <span class="chip" data-f="high">★ 最对口</span>
      <span class="chip" data-f="互联网/科技">互联网/科技</span>
      <span class="chip" data-f="网络安全">网络安全</span>
      <span class="chip" data-f="金融/运营商/电网">金融/运营商/电网</span>
      <span class="chip" data-f="制造/半导体/汽车">制造/半导体/汽车</span>
      <span class="chip" data-f="low">看情况</span>
    </div>
    <div class="grid" id="g-new"></div>
    <div id="applied-bar" class="hide" style="margin-top:13px;font-size:12.5px;color:#4e5969;background:#fff;border:1px solid #e5e6eb;border-radius:10px;padding:11px 15px">
      你标记了 <b id="applied-n">0</b> 家为「已投」。
      <a href="javascript:void(0)" id="applied-save" style="color:#d4380d;text-decoration:none;margin-left:8px;font-weight:600">⤓ 保存名单到本地（永久）</a>
      <a href="javascript:void(0)" id="applied-undo" style="color:#3b6ef5;text-decoration:none;margin-left:8px">撤销浏览器标记</a>
      <a href="javascript:void(0)" id="applied-export" style="color:#3b6ef5;text-decoration:none;margin-left:8px">复制名单</a>
      <span id="applied-pending" class="hide" style="color:#d4380d;font-weight:600">（有 <b id="applied-pending-n">0</b> 家还没存进磁盘，点上面「保存名单」防丢失）</span>
      <div style="margin-top:6px;color:#a9aeb8">已存进 <code>手动已投标记.txt</code> 的公司下次生成自动剔除、永久生效；只存在浏览器的会被清缓存弄丢。</div>
    </div>
    <div id="moved-box" class="hide">
      <h2 class="sec g">__N_MOVED__ 家已投过，已自动从本页剔除</h2>
      <table><thead><tr><th style="width:170px">通道里的名字</th><th style="width:170px">匹配到的已投名字</th><th style="width:90px">依据</th><th>分类</th></tr></thead><tbody id="g-moved"></tbody></table>
    </div>
    <h2 class="sec g">__N_UNCF__ 家暂未查到 2027 届官方校招入口</h2>
    <table><thead><tr><th style="width:150px">公司</th><th style="width:130px">分类</th><th>说明</th></tr></thead><tbody id="g-uncf"></tbody></table>
  </div>

  <div id="pane-ref" class="hide">
    <div class="toolbar">
      <input type="text" id="q5" placeholder="搜索公司 / 内推码…">
      <span class="chip on" data-f="all">全部</span>
      <span class="chip" data-f="mine">我已投过</span>
      <span class="chip" data-f="fresh">还没投</span>
      <span class="chip" data-f="high">来源最可靠</span>
      <span class="chip" data-f="互联网/科技">互联网/科技</span>
      <span class="chip" data-f="游戏">游戏</span>
      <span class="chip" data-f="网络安全/通信">网络安全/通信</span>
      <span class="chip" data-f="制造/半导体/汽车">制造/半导体/汽车</span>
      <span class="chip" data-f="制造/消费电子">制造/消费电子</span>
      <span class="chip" data-f="金融/银行">金融/银行</span>
    </div>
    <div class="note" style="margin-bottom:13px">
      <b>点内推码即可复制。</b>公开码有有效期和次数限制，一个填不上就换下一个；0 与 O、1 与 l、5 与 S 肉眼易混，贴进去前对照原表核一遍。
      <b>凡是要你交钱才给内推的，一律是诈骗。</b>
    </div>
    <div class="grid" id="g-ref"></div>
    <h2 class="sec g">__N_NOREF__ 家确认无需内推码 / 没有内推机制（别白费劲找了）</h2>
    <table><thead><tr><th style="width:160px">公司</th><th style="width:130px">分类</th><th>说明</th><th style="width:80px">入口</th></tr></thead><tbody id="g-noref"></tbody></table>
  </div>

  <div id="pane-dead" class="hide">
    <div class="toolbar">
      <input type="text" id="q4" placeholder="搜索公司 / 事项…">
      <span class="chip on" data-f="all">全部</span>
      <span class="chip" data-f="未通过">未通过</span>
      <span class="chip" data-f="已考">已考待结果</span>
      <span class="chip" data-f="已过期">已过期</span>
    </div>
    <table><thead><tr><th style="width:90px">状态</th><th style="width:170px">公司</th><th>岗位 / 事项</th><th style="width:110px">时间</th><th style="width:230px">说明</th></tr></thead><tbody id="g-dead"></tbody></table>
  </div>

  <footer>
    每日 09:00 自动扫描邮箱更新待办　|　每日 09:30 自动比对台账 xlsx 并补充校招官网<br>
    点「可补投通道」里的 ★ 标记＝岗位方向与你（网络工程 / 运维 / 安全）高度对口<br>
    内推码均来自公开渠道（高校就业网 / 牛客员工帖 / 聚合帖），有有效期与次数限制，失效请换下一个
  </footer>
</div>
<div id="toast"></div>
<div id="frameLayer" class="hide">
  <div class="fl-bar">
    <span class="fl-title" id="flTitle">官网</span>
    <input class="fl-url" id="flUrl" readonly>
    <button id="flRefresh" class="ghost">刷新</button>
    <button id="flCopy" class="ghost">复制链接</button>
    <button id="flExt">在系统浏览器打开 ↗</button>
    <button id="flClose" class="close">✕ 返回工作台</button>
  </div>
  <div class="fl-warn" id="flWarn">⚠️ 该网站设置了禁止内嵌（X-Frame-Options），无法在阿禾里直接显示——这是网站自己的安全策略，并非阿禾的问题。下方链接可直接打开；或在阿禾里「复制链接」后去浏览器粘贴（投递需你已登录的账号态）。<br><a id="flLink" href="#" target="_blank" rel="noopener" style="color:#1f6feb;font-weight:600;text-decoration:underline">打开该网站 ↗</a></div>
  <iframe id="frameFrame" referrerpolicy="no-referrer" sandbox="allow-same-origin allow-scripts allow-forms allow-popups"></iframe>
</div>

<script>
const TODOS = __J_TODO__;
const PEND  = __J_PEND__;
const MINE  = __J_MINE__;
const NEWC  = __J_NEW__;
const UNCF  = __J_UNCF__;
const DEAD  = __J_DEAD__;
const REF   = __J_REF__;
const NOREF = __J_NOREF__;
const MOVED = __J_MOVED__;

function esc(s){return (s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]);}
function cdText(iso){
  const t = new Date(iso).getTime() - Date.now();
  if (t < 0) return {cls:'over', txt:'已过 ' + fmt(-t)};
  return {cls: t < 3*864e5 ? 'hot' : (t < 7*864e5 ? 'warn' : 'ok'), txt:'剩 ' + fmt(t)};
}
function fmt(ms){
  let s = Math.floor(ms/1000), d = Math.floor(s/86400), h = Math.floor(s%86400/3600), m = Math.floor(s%3600/60);
  if (d > 0) return d + ' 天 ' + h + ' 小时';
  if (h > 0) return h + ' 小时 ' + m + ' 分';
  return m + ' 分钟';
}

function todoCard(d){
  const k = tkey(d);
  const done = DONE.has(k);
  const c = cdText(d.iso);
  const main = d.url
    ? '<a class="btn" href="'+d.url+'" data-ext="'+d.url+'" data-title="'+esc(d.comp)+'">立即处理 ↗</a>'
    : '<a class="btn na">无直链</a>';
  const act = done
    ? '<a class="btn g" href="javascript:void(0)" data-undone="'+esc(k)+'" title="点一下恢复为待办">↩ 恢复</a>'
    : '<a class="btn g" href="javascript:void(0)" data-done="'+esc(k)+'" title="处理完点一下，从待办里划掉">✓ 已处理</a>';
  const btns = '<div class="btns">'+main+act+'</div>';
  const ex = (d.extra||[]).length
    ? '<div class="exlinks">'+d.extra.map(e=>'<a href="'+e.url+'" data-ext="'+e.url+'" data-title="'+esc(e.label)+'">'+esc(e.label)+'</a>').join('')+'</div>'
    : '';
  return '<div class="card '+c.cls+'"><h3>'+esc(d.comp)+'<span class="tag type">'+esc(d.type)+'</span>'
    + (done?'<span class="mine">已处理</span>':'') + '</h3>'
    + '<div class="role">'+esc(d.item)+'</div>'
    + '<div><span class="cd '+c.cls+'">'+c.txt+'</span> <span class="meta">截止 '+esc(d.dl)+'</span></div>'
    + '<div class="note">'+esc(d.note)+'</div>' + btns + ex + '</div>';
}
function pendCard(d){
  const k = pkey(d);
  const done = DONE.has(k);
  const main = d.url ? '<a class="btn g" href="'+d.url+'" data-ext="'+d.url+'" data-title="'+esc(d.comp)+'">打开 ↗</a>' : '';
  const act = done
    ? '<a class="btn g" href="javascript:void(0)" data-undone="'+esc(k)+'" title="点一下恢复为待办">↩ 恢复</a>'
    : '<a class="btn g" href="javascript:void(0)" data-done="'+esc(k)+'" title="处理完点一下，从待办里划掉">✓ 已处理</a>';
  const b = '<div class="btns">'+main+act+'</div>';
  return '<div class="card"><h3>'+esc(d.comp)+'<span class="tag type">'+esc(d.type)+'</span>'
    + (done?'<span class="mine">已处理</span>':'') + '</h3>'
    + '<div class="role">'+esc(d.item)+'</div>' + b + '</div>';
}
function mineCard(d){
  const has = !!d.url;
  return '<div class="card '+d.urg+'"><h3>'+esc(d.name)+'<span class="tag">台账#'+esc(d.seq)+'</span></h3>'
    + '<div class="role">'+esc(d.role)+'</div>'
    + '<div class="meta"><span>📍 '+esc(d.loc||'—')+'</span><span>状态：'+esc(d.status||'—')+'</span></div>'
    + '<div><span class="cd '+d.urg+'">'+esc(d.dlTxt)+'</span></div>'
    + '<div class="note">'+esc(d.note)+'</div>'
    + '<div class="btns"><a class="btn '+(has?'':'na')+'" href="'+(has?d.url:'javascript:void(0)')+'"'+(has?' data-ext="'+d.url+'" data-title="'+esc(d.name)+'"':'')+'>'+(has?'校招官网 ↗':'官网未确认')+'</a></div></div>';
}
function newCard(d){
  const star = d.fit==='high' ? '<span class="tag hi">★ 最对口</span>' : (d.fit==='low' ? '<span class="tag">看情况</span>' : '');
  return '<div class="card '+d.urg+'"><h3>'+esc(d.name)+star+'</h3>'
    + '<div class="meta"><span>'+esc(d.cat)+'</span></div>'
    + '<div><span class="cd '+d.urg+'">'+esc(d.dlTxt)+'</span></div>'
    + '<div class="note">'+esc(d.note)+'</div>'
    + '<div class="btns"><a class="btn" href="'+d.url+'" data-ext="'+d.url+'" data-title="'+esc(d.name)+'">去投递 ↗</a>'
    + '<a class="btn g" href="javascript:void(0)" data-mark="'+esc(d.name)+'" title="投完点一下，从待投列表移出">✓ 已投</a></div></div>';
}

const SRCTXT = {high:'高校就业网·官方简章', mid:'牛客员工帖', low:'聚合帖·待验证'};
function refCard(d){
  const bar = d.codes.length
    ? '<div class="codebar">' + d.codes.map(c=>'<span class="code" title="点击复制">'+esc(c)+'</span>').join('') + '</div>'
    : '<div class="codebar"><span class="code na">'+esc(d.raw)+'</span></div>';
  // 已投 = 台账算的 d.mine ∪ 浏览器实时标记（与 renderRef 的 liveMine 一致）
  const isMine = d.mine || appliedTo(d.name);
  // 浏览器侧可撤销的标记；磁盘底图（手动已投标记.txt）与台账的不可在浏览器撤销
  let bm = null;
  for(const m of APPLIED){ if(isSame(d.name, m) && !BASE_APPLIED.includes(m)){ bm = m; break; } }
  const toggle = isMine
    ? (bm
        ? '<a class="btn g" href="javascript:void(0)" data-unmark="'+esc(bm)+'" title="点一下撤销「已投」标记">✓ 已投（点击撤销）</a>'
        : '<a class="btn g" href="javascript:void(0)" data-nomark="1" title="来自 Excel 台账，需改台账才生效">已投过（台账）</a>')
    : '<a class="btn g" href="javascript:void(0)" data-mark="'+esc(d.name)+'" title="投完点一下，可补投通道里的这家会同步隐藏">✓ 标为已投</a>';
  return '<div class="card"><h3>'+esc(d.name)
    + '<span class="src '+d.src+'" title="'+esc(SRCTXT[d.src])+'">'+esc(SRCTXT[d.src])+'</span>'
    + '<span class="mine '+(isMine?'y':'')+'">'+(isMine?'已投过':'未投')+'</span></h3>'
    + '<div class="meta"><span>'+esc(d.cat)+'</span></div>'
    + bar
    + '<div class="note">'+esc(d.note)+'</div>'
    + '<div class="btns"><a class="btn g" href="'+d.url+'" data-ext="'+d.url+'" data-title="'+esc(d.name)+'">去校招官网 ↗</a>' + toggle + '</div></div>';
}

const S = {todo:'', mine:'', new:'', dead:'', ref:''};
const F = {todo:'all', mine:'all', new:'all', dead:'all', ref:'all'};

function renderTodo(){
  const l = TODOS.filter(d=>{
    const okT = F.todo==='all' ? true : (F.todo==='hot' ? (new Date(d.iso)-Date.now())<7*864e5 : d.type===F.todo);
    const ok = okT && (!S.todo || (d.comp+d.item+d.note).toLowerCase().includes(S.todo));
    return ok && (SHOW_DONE || !DONE.has(tkey(d)));
  });
  document.getElementById('g-todo').innerHTML = l.map(todoCard).join('') || '<div class="empty">没有匹配的待办</div>';
  const pl = PEND.filter(d=> SHOW_DONE || !DONE.has(pkey(d)));
  document.getElementById('g-pend').innerHTML = pl.map(pendCard).join('');
  // 已处理提示条 + 待办计数（只算未处理的）
  const bar = document.getElementById('done-bar');
  if (bar){
    bar.classList.toggle('hide', DONE.size===0);
    document.getElementById('done-n').textContent = String(DONE.size);
    const showL = document.getElementById('done-show');
    if (showL) showL.textContent = SHOW_DONE ? '隐藏已处理' : '显示已处理';
  }
  const left = TODOS.filter(d=>!DONE.has(tkey(d))).length;
  const sn = document.getElementById('stat-todo'), tn = document.getElementById('tab-todo-n');
  if (sn) sn.textContent = String(left);
  if (tn) tn.textContent = String(left);
}
function renderMine(){
  const l = MINE.filter(d=>{
    const ok = F.mine==='all' ? true : (F.mine==='hot' ? d.urg==='hot' : d.cat===F.mine);
    return ok && (!S.mine || (d.name+d.role+d.loc+d.note).toLowerCase().includes(S.mine));
  });
  document.getElementById('g-mine').innerHTML = l.map(mineCard).join('') || '<div class="empty">没有匹配的公司</div>';
}
// 已投真相：BASE_APPLIED = 生成时从磁盘「手动已投标记.txt」烤入的底图（永久，不怕浏览器清缓存）
// APPLIED = 底图 ∪ 本机浏览器临时标记；刷新/重新生成后底图仍在，不会丢
const BASE_APPLIED = __BASE_APPLIED__;
const LSKEY = 'qy_applied_v1';
let APPLIED = new Set([...BASE_APPLIED]);
try { JSON.parse(localStorage.getItem(LSKEY) || '[]').forEach(x=>APPLIED.add(x)); } catch(e) {}
function saveApplied(){ try { localStorage.setItem(LSKEY, JSON.stringify([...APPLIED])); } catch(e) {} }

// 待办「已处理」标记（本机浏览器）—— 键用"类型|公司|事项"拼，改动事项文字会重置标记
const DKEY = 'qy_done_v1';
let DONE = new Set();
try { JSON.parse(localStorage.getItem(DKEY) || '[]').forEach(x=>DONE.add(x)); } catch(e) {}
function saveDone(){ try { localStorage.setItem(DKEY, JSON.stringify([...DONE])); } catch(e) {} }
const tkey = d => ['T', d.type||'', d.comp||'', d.item||''].join('|');
const pkey = d => ['P', d.type||'', d.comp||'', d.item||''].join('|');
let SHOW_DONE = false;
// —— 公司名同指判断（复刻 Python is_same），用于「✓已投」实时联动内推码 tab ——
const _NOTSAME = [["京东","京东方"],["京东","京东物流"],["腾讯","腾讯音乐"],["腾讯","腾讯健康"],["阿里","阿里健康"],["中国通号","通号"],["中国电信","中国移动"],["中国电信","中国联通"],["招商银行","招银网络科技"],["中国工商银行","中国建设银行"],["中国工商银行","中国农业银行"],["中国工商银行","交通银行"],["中国工商银行","中国邮政储蓄银行"],["中国工商银行","中信银行"],["中国工商银行","浦发银行"],["中国工商银行","兴业银行"],["中国工商银行","中国民生银行"],["东风汽车","长安汽车"],["东风汽车","上汽集团"],["东风汽车","广汽集团"],["东风汽车","吉利控股"],["东风汽车","小鹏汽车"],["东风汽车","理想汽车"],["东风汽车","蔚来"],["东风汽车","比亚迪"],["通号工程局集团","通号工程电气化局"],["通号工程局集团","通号低空"],["通号工程电气化局","通号低空"],["通号低空","北京现代通号工程咨询"]];
const _ALIAS = [["中国移动湖北公司","中国移动"],["湖北移动","中国移动"],["中国电信","中国电信"],["千问（阿里巴巴）","阿里巴巴"],["智元机器人（AGIBOT）","智元机器人"],["网易（互娱）","网易"],["湖北亿纬动力（亿纬锂能）","亿纬锂能"],["亿纬锂能（社招）","亿纬锂能"],["腾讯音乐 TME","腾讯音乐"],["腾讯音乐TME","腾讯音乐"]];
const _SHORT = ["小米","海尔","美的","格力","华为","中兴","联想","大疆","蔚来","吉利","百度","美团","腾讯","网易","字节","京东","顺丰","海信","长虹","比亚迪","宁德","三一","浪潮","金蝶","长城","长安","广汽","上汽","东风","奇瑞","海康","大华","oppo","vivo","携程","滴滴","快手","微博","知乎","拼多多"];
function _norm(s){ s=String(s||''); for(const ch of " （）()·-/&"){ s=s.split(ch).join(''); } return s.toLowerCase(); }
function isSame(a,b){
  const na=_norm(a), nb=_norm(b);
  if(!na||!nb) return false;
  if(na===nb) return true;
  for(const p of _ALIAS){ const nx=_norm(p[0]), ny=_norm(p[1]); if((na===nx&&nb===ny)||(na===ny&&nb===nx)) return true; }
  for(const p of _NOTSAME){ const nx=_norm(p[0]), ny=_norm(p[1]); if((nx===na||nx===nb)&&(ny===na||ny===nb)) return false; }
  const short=(na.length<=nb.length)?na:nb, long=(na.length<=nb.length)?nb:na;
  if(short.length>=3 && long.indexOf(short)>=0) return true;
  if(na.length>=4 && nb.length>=4 && na.slice(0,4)===nb.slice(0,4)) return true;
  if(_SHORT.indexOf(short)>=0 && long.indexOf(short)===0) return true;
  return false;
}
function appliedTo(name){ for(const m of APPLIED){ if(isSame(name, m)) return true; } return false; }

function renderNew(){
  const l = NEWC.filter(d=>{
    const ok = F.new==='all' ? true : (F.new==='high'||F.new==='low' ? d.fit===F.new : d.cat===F.new);
    return ok && !appliedTo(d.name) && (!S.new || (d.name+d.note+d.cat).toLowerCase().includes(S.new));
  });
  document.getElementById('g-new').innerHTML = l.map(newCard).join('') || '<div class="empty">没有匹配的通道</div>';
  document.getElementById('g-uncf').innerHTML = UNCF.map(u=>'<tr><td><b>'+esc(u.name)+'</b></td><td class="c">'+esc(u.cat)+'</td><td class="c">'+esc(u.note)+'</td></tr>').join('');
  const bar = document.getElementById('applied-bar');
  bar.classList.toggle('hide', APPLIED.size===0);
  document.getElementById('applied-n').textContent = String(APPLIED.size);
  const pend = [...APPLIED].filter(x=>!BASE_APPLIED.includes(x));
  const pEl = document.getElementById('applied-pending');
  if (pEl){ pEl.classList.toggle('hide', pend.length===0); document.getElementById('applied-pending-n').textContent = String(pend.length); }
  const left = String(NEWC.length - NEWC.filter(d=>appliedTo(d.name)).length);
  const sn = document.getElementById('stat-new'), tn = document.getElementById('tab-new-n');
  if (sn) sn.textContent = left;
  if (tn) tn.textContent = left;
  if (MOVED.length){
    document.getElementById('moved-box').classList.remove('hide');
    document.getElementById('g-moved').innerHTML = MOVED.map(m=>
      '<tr><td><b>'+esc(m.name)+'</b></td><td class="c">'+esc(m.ledger)+'</td>'
      + '<td class="c"><span class="pill '+(m.src==='台账'?'g':'d')+'">'+esc(m.src)+'</span></td>'
      + '<td class="c">'+esc(m.cat)+'</td></tr>').join('');
  }
}
document.addEventListener('click', e=>{
  const a = e.target.closest('[data-mark]');
  if (!a) return;
  e.preventDefault();
  APPLIED.add(a.dataset.mark); saveApplied(); renderNew(); renderRef();
  say('已标记「'+a.dataset.mark+'」为已投，可补投与内推码同步更新');
});
document.addEventListener('click', e=>{
  const a = e.target.closest('[data-unmark]');
  if (!a) return;
  e.preventDefault();
  APPLIED.delete(a.dataset.unmark); saveApplied(); renderNew(); renderRef();
  say('已撤销「'+a.dataset.unmark+'」的已投标记');
});
document.addEventListener('click', e=>{
  const a = e.target.closest('[data-nomark]');
  if (!a) return;
  e.preventDefault();
  say('这家来自 Excel 台账，请在台账里改；浏览器只能标记台账里没有的公司');
});
document.addEventListener('click', e=>{
  const a = e.target.closest('[data-done]');
  if (!a) return;
  e.preventDefault();
  DONE.add(a.dataset.done); saveDone(); renderTodo();
  say('已标记处理完成，从待办划掉');
});
document.addEventListener('click', e=>{
  const a = e.target.closest('[data-undone]');
  if (!a) return;
  e.preventDefault();
  DONE.delete(a.dataset.undone); saveDone(); renderTodo();
  say('已恢复为待办');
});
document.getElementById('done-undo').addEventListener('click', ()=>{
  DONE.clear(); saveDone(); renderTodo(); say('已恢复全部已处理项');
});
document.getElementById('done-show').addEventListener('click', ()=>{
  SHOW_DONE = !SHOW_DONE; renderTodo();
  say(SHOW_DONE ? '已显示已处理项' : '已隐藏已处理项');
});
document.getElementById('applied-undo').addEventListener('click', ()=>{
  APPLIED = new Set(BASE_APPLIED); saveApplied(); renderNew(); renderRef(); say('已撤销本次浏览器内手动标记（磁盘名单保留）');
});
document.getElementById('applied-save').addEventListener('click', ()=>{
  const all = [...APPLIED];
  const header = "# 手动标记为「已投」的公司，每行一个，会被自动从「可补投通道」剔除\n# 写法：直接写公司名，可用简称；# 开头为注释\n\n";
  const body = header + all.join("\n") + (all.length?"\n":"");
  const blob = new Blob([body], {type:"text/plain;charset=utf-8"});
  const aEl = document.createElement('a'); aEl.href = URL.createObjectURL(blob);
  aEl.download = "手动已投标记.txt"; document.body.appendChild(aEl); aEl.click();
  document.body.removeChild(aEl); URL.revokeObjectURL(aEl.href);
  say("已导出 "+all.length+" 家到「手动已投标记.txt」，把它存进 D:/y'world/求职邮件追踪/ 覆盖同名文件即永久生效");
});
document.getElementById('applied-export').addEventListener('click', ()=>{
  const txt = [...APPLIED].join('\n');
  const done = ()=> say('已复制 '+APPLIED.size+' 个公司名，粘进「手动已投标记.txt」即可长期生效');
  if (navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(txt).then(done).catch(()=>{ prompt('复制下面的公司名：', txt); });
  } else { prompt('复制下面的公司名：', txt); }
});
function renderRef(){
  const liveMine = d => d.mine || appliedTo(d.name);
  const l = REF.filter(d=>{
    const isMine = liveMine(d);
    let ok = true;
    if (F.ref==='mine') ok = isMine;
    else if (F.ref==='fresh') ok = !isMine;
    else if (F.ref==='high') ok = d.src==='high';
    else if (F.ref!=='all') ok = d.cat===F.ref;
    return ok && (!S.ref || (d.name+d.raw+d.note).toLowerCase().includes(S.ref));
  });
  document.getElementById('g-ref').innerHTML = l.map(d=>refCard(Object.assign({}, d, {mine: liveMine(d)}))).join('') || '<div class="empty">没有匹配的公司</div>';
  document.getElementById('g-noref').innerHTML = NOREF.map(n=>
    '<tr><td><b>'+esc(n.name)+'</b></td><td class="c">'+esc(n.cat)+'</td><td class="c">'+esc(n.note)+'</td>'
    + '<td>'+(n.url?'<a href="'+n.url+'" data-ext="'+n.url+'" data-title="'+esc(n.name)+'">入口 ↗</a>':'—')+'</td></tr>').join('');
}
function renderDead(){
  const map = {'未通过':'a','已考':'d','已过期':'c'};
  const l = DEAD.filter(d=>{
    const ok = F.dead==='all' ? true : d.cat===F.dead;
    return ok && (!S.dead || (d.comp+d.item+d.note).toLowerCase().includes(S.dead));
  });
  document.getElementById('g-dead').innerHTML = l.map(d=>'<tr><td><span class="pill '+map[d.cat]+'">'+esc(d.cat)+'</span></td><td><b>'+esc(d.comp)+'</b></td><td>'+esc(d.item)+'</td><td class="c">'+esc(d.time)+'</td><td class="c">'+esc(d.note)+'</td></tr>').join('') || '<tr><td colspan="5" class="empty">没有匹配记录</td></tr>';
}

const RENDER = {todo:renderTodo, mine:renderMine, new:renderNew, ref:renderRef, dead:renderDead};
document.querySelectorAll('.tab').forEach(t=>t.addEventListener('click',()=>{
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));
  t.classList.add('on');
  ['todo','mine','new','ref','dead'].forEach(k=>document.getElementById('pane-'+k).classList.toggle('hide', k!==t.dataset.t));
}));
[['q1','todo'],['q2','mine'],['q3','new'],['q4','dead'],['q5','ref']].forEach(([id,k])=>{
  document.getElementById(id).addEventListener('input', e=>{S[k]=e.target.value.trim().toLowerCase(); RENDER[k]();});
});
document.querySelectorAll('.chip').forEach(c=>{
  const pane = c.closest('div[id^=pane]').id.replace('pane-','');
  c.addEventListener('click',()=>{
    c.parentElement.querySelectorAll('.chip').forEach(x=>x.classList.remove('on'));
    c.classList.add('on'); F[pane]=c.dataset.f;
    RENDER[pane]();
  });
});
const toast = document.getElementById('toast');
let toastT;
function say(msg){
  toast.textContent = msg; toast.classList.add('on');
  clearTimeout(toastT); toastT = setTimeout(()=>toast.classList.remove('on'), 1400);
}
document.addEventListener('click', e=>{
  const s = e.target.closest('.code');
  if (!s || s.classList.contains('na')) return;
  const t = s.textContent.trim();
  const done = ()=>say('已复制：' + t);
  if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(t).then(done, ()=>fallback(t, done));
  else fallback(t, done);
});
function fallback(t, done){
  const ta = document.createElement('textarea');
  ta.value = t; ta.style.position='fixed'; ta.style.opacity='0';
  document.body.appendChild(ta); ta.select();
  try { document.execCommand('copy'); done(); } catch(e){ say('复制失败，请手动选中'); }
  document.body.removeChild(ta);
}
// 内置浏览器浮层：点击「去投递/官网/测评」等外链，在阿禾内独立显示网页，可关闭返回工作台
let _flTimer = null;
function openInFrame(url, title){
  if (!url || url.indexOf('http') !== 0) return;
  const layer = document.getElementById('frameLayer');
  const frame = document.getElementById('frameFrame');
  const warn  = document.getElementById('flWarn');
  document.getElementById('flTitle').textContent = title || '官网';
  document.getElementById('flUrl').value = url;
  document.getElementById('flLink').href = url;
  warn.classList.remove('show');
  layer.classList.remove('hide');
  frame.src = 'about:blank';
  frame.src = url;
  clearTimeout(_flTimer);
  _flTimer = setTimeout(()=>{
    try {
      if (frame.contentWindow.location.href === 'about:blank') warn.classList.add('show');
    } catch(e) { /* 跨域=正常加载，无需提示 */ }
  }, 4000);
  window.scrollTo(0,0);
}
document.getElementById('flClose').addEventListener('click', ()=>{
  document.getElementById('frameLayer').classList.add('hide');
  document.getElementById('frameFrame').src = 'about:blank';
});
document.getElementById('flRefresh').addEventListener('click', ()=>{
  const f = document.getElementById('frameFrame'), u = document.getElementById('flUrl').value;
  f.src = 'about:blank'; f.src = u;
  document.getElementById('flWarn').classList.remove('show');
});
document.getElementById('flExt').addEventListener('click', ()=>{
  const u = document.getElementById('flUrl').value;
  let w=null; try{ w=window.open(u,'_blank','noopener,noreferrer'); }catch(e){ w=null; }
  if(!w){ const d=()=>say('已复制链接，请在浏览器打开 ↗'); if(navigator.clipboard&&window.isSecureContext) navigator.clipboard.writeText(u).then(d,()=>fallback(u,d)); else fallback(u,d); }
});
document.getElementById('flCopy').addEventListener('click', ()=>{
  const u = document.getElementById('flUrl').value;
  const d=()=>say('已复制链接 ✓'); if(navigator.clipboard&&window.isSecureContext) navigator.clipboard.writeText(u).then(d,()=>fallback(u,d)); else fallback(u,d);
});
document.addEventListener('click', e=>{
  const a = e.target.closest('[data-ext]');
  if (!a) return;
  e.preventDefault();
  openInFrame(a.getAttribute('data-ext'), a.getAttribute('data-title') || a.textContent.trim());
});
renderTodo(); renderMine(); renderNew(); renderRef(); renderDead();
setInterval(renderTodo, 60000);
</script>
</body>
</html>"""

J = lambda o: json.dumps(o, ensure_ascii=False)
n_hot = len([x for x in mine if x["urg"] == "hot"]) + len([x for x in newch if x["urg"] == "hot"])
html = (html
    .replace("__J_TODO__", J(todos)).replace("__J_PEND__", J(pending))
    .replace("__J_MINE__", J(mine)).replace("__J_NEW__", J(newch))
    .replace("__J_UNCF__", J(uncf)).replace("__J_DEAD__", J(dead))
    .replace("__J_REF__", J(refs)).replace("__J_NOREF__", J(noref)).replace("__J_MOVED__", J(_moved))
    .replace("__N_TODO__", str(len(todos))).replace("__N_PEND__", str(len(pending)))
    .replace("__N_MINE__", str(len(mine))).replace("__N_NEW__", str(len(newch)))
    .replace("__N_UNCF__", str(len(uncf))).replace("__N_DEAD__", str(len(dead)))
    .replace("__N_REF__", str(len(refs))).replace("__N_NOREF__", str(len(noref)))
    .replace("__N_MOVED__", str(len(_moved)))
    .replace("__BASE_APPLIED__", J(_manual_names))
    .replace("__N_HOT__", str(n_hot)))

# ---------- 导出纯文本内推码清单 ----------
SRCNAME = {"high": "高校就业网/官方简章", "mid": "牛客员工帖", "low": "聚合帖·待验证"}
L = []
L.append("# 2027 届秋招内推码清单\n")
L.append("> 姜艺（长江大学 · 网络工程）｜ 联网核实于 **2026-09-26** ｜ 共 **{}** 家有公开内推码，另有 **{}** 家确认无需/无内推机制\n".format(len(refs), len(noref)))
L.append("## 使用前必读\n")
L.append("1. **内推码有有效期和次数限制**，看到就尽快投，别收藏吃灰。一个填不上就换下一个。")
L.append("2. **0 与 O、1 与 l、5 与 S 肉眼极易看错**，贴进网申表前对照原表核一遍。填错了内推等于白拿。")
L.append("3. **凡是要你交钱才给内推的，一律是诈骗。** 华为、中国移动等官方已明确警示。")
L.append("4. 可信度标注：`高校就业网/官方简章` > `牛客员工帖` > `聚合帖·待验证`。标了待验证的请先小范围试投确认。\n")

L.append("## 一、有公开内推码（{} 家）\n".format(len(refs)))
cur = None
for r in refs:
    if r["cat"] != cur:
        cur = r["cat"]
        L.append("\n### {}\n".format(cur))
        L.append("| 公司 | 内推码 | 可信度 | 说明 |")
        L.append("|---|---|---|---|")
    codes = " ／ ".join("`{}`".format(c) for c in r["codes"]) if r["codes"] else r["raw"]
    flag = "（已投过）" if r["mine"] else ""
    L.append("| {}{} | {} | {} | {} |".format(r["name"], flag, codes, SRCNAME[r["src"]], r["note"].replace("\n", " ")))

L.append("\n## 二、确认无需内推码 / 没有内推机制（{} 家）\n".format(len(noref)))
L.append("这些别再花时间找码了，直接官网投。\n")
L.append("| 公司 | 分类 | 说明 |")
L.append("|---|---|---|")
for n in noref:
    L.append("| {} | {} | {} |".format(n["name"], n["cat"], n["note"].replace("\n", " ")))

L.append("\n## 三、最该先投的（内推码 + 岗位对口 + 时间紧）\n")
L.append("| 公司 | 内推码 | 为什么优先 |")
L.append("|---|---|---|")
L2 = []
L2.append("| 公司 | 内推码 | 为什么优先 |")
L2.append("|---|---|---|")
for name, code, why in [
    ("蔚来 NIO", "R6D4SHC", "数字技术类含「平台规划、开发与运维」，9 月底前网申"),
    ("大疆 DJI", "DSGz7tGD", "27 届「拓疆者」含信息安全岗，每人限投 1 个职位"),
    ("深信服", "NTAWwLF", "出自高校就业网正式简章，27 届校招进行中"),
    ("亚信安全", "V2NRKVF", "★ 全部岗位免笔试，限投 1 个职位，10-30 截止"),
    ("京东方 BOE", "FY34V", "岗位列表明确含信息安全专员，招满即止"),
    ("格力电器", "CGREE77820", "信息技术类明确含信息安全岗，多校就业网背书"),
    ("美的集团", "M4I451", "八大职类含信息技术类，已投递也能在个人中心补填"),
    ("小鹏汽车", "GWVHCUY", "13-16 大岗位类别含数据智能方向"),
    ("吉利控股", "DSPW7fqP", "九大方向明确含 IT/互联网类，10-31 截止"),
    ("寒武纪", "NTAr8IQ", "需求专业含网络空间安全，推荐码发布者可查进度"),
    ("OPPO", "X3448036", "出自华中农业大学就业网官方简章，最稳妥"),
    ("中兴通讯", "NTAXptH", "通信大厂，注意已投过实习/领军计划就别填码"),
]:
    L2.append("| {} | `{}` | {} |".format(name, code, why))
L[-1:] = L2

L.append("\n## 四、拿到更多内推码的渠道\n")
L.append("1. **牛客网内推广场** — `nowcoder.com` 搜索「27届 内推」，帖子每天更新，评论区可直接问发布者要码")
L.append("2. **高校就业网** — 华中师大 `ccnu.91wllm.cn`、兰州大学、温州大学等就业网发布的招聘简章里常附官方内推码，可信度最高")
L.append("3. **小红书 / 脉脉** — 搜「公司名 + 内推码」，注意甄别营销号；优先找带员工认证标识的")
L.append("4. **校园大使 / 学长学姐** — 各公司校园大使手里有专属码，且能查进度，比公开码靠谱")
L.append("5. **长江大学就业信息网 + 学院就业群** — 来校宣讲的企业常把内推码直接发到群里\n")

L.append("---\n")
L.append("本清单由脚本 `build_workbench.py` 的 REF / NOREF 两个列表生成，改数据后重跑脚本即可同步更新工作台。")

p2 = os.path.join(OUT_DIR, "内推码清单.md")
with open(p2, "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("内推码清单已生成:", p2)

p = os.path.join(OUT_DIR, "秋招工作台.html")
with open(p, "w", encoding="utf-8") as f:
    f.write(html)
print("工作台已生成:", p)
print("待办", len(todos), "| 无截止", len(pending), "| 已投", len(mine), "| 可补投", len(newch), "| 未确认", len(uncf), "| 已结束", len(dead))
print("内推码", len(refs), "家（其中已投过", len([x for x in refs if x['mine']]), "家）| 确认无需内推", len(noref), "家")
print("去重：可补投通道原", len(NEW), "家 → 剔除已投", len(_moved), "家 → 剩", len(newch), "家")
print("  已投依据：台账", len(_ledger_names), "家 + 手动名单", len(_manual_names), "家")
if _manual_names:
    print("  手动名单内容：", "、".join(_manual_names))
if _moved:
    for m in _moved:
        print("   已剔除:", m["name"], "(台账:", m["ledger"] + ")")
