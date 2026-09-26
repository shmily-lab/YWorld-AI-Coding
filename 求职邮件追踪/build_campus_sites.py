# -*- coding: utf-8 -*-
"""
生成《已投递公司校招官网清单》(Markdown) 与《校招官网看板》(HTML)
数据来自 WPS 云盘《工作计划完成统计表1.xlsx》「五月」sheet 的投递台账
"""
import datetime, os

OUT_DIR = r"D:\y'world\求职邮件追踪"
os.makedirs(OUT_DIR, exist_ok=True)

# seq, 公司, 岗位, 地点, 台账状态, 分类, URL, 官网备注, 截止日期(YYYY-MM-DD 或 '')
DATA = [
# ---- 互联网 / 科技 ----
("75","字节跳动","骨干网络运维/网络运维工程师/云网络运维/DCN 等 7 岗（可再投）","北京等","未标注","互联网/科技","https://jobs.bytedance.com/campus","2027届8月3日开启；官方口径通道截止2027-05-31，招满即止；全年4次投递机会",""),
("77","腾讯","网络技术","深圳等","测试完成","互联网/科技","https://join.qq.com","2027校招8月11日开启；投递项目须选「应届毕业生—2027校园招聘」，技术类下有安全技术岗",""),
("88","百度","软件测试工程师","北京等","未标注","互联网/科技","https://talent.baidu.com/jobs","2027届7月9日开启；通道持续开放，一次投1个职位但次数不限",""),
("37","美团","运维开发工程师","北京等","过初筛，进笔试并完成","互联网/科技","https://zhaopin.meituan.com/web/campus","2027届8月17日开启；网申截止 2026-10-31，最多填3个志愿","2026-10-31"),
("72","京东","技术运维工程师、安全工程师","北京等","测试完成；另有一场安全工程师笔试","互联网/科技","https://campus.jd.com","2027校招8月3日开启；网申截止 2026-11-30；首次引入AI面试","2026-11-30"),
("22","小米","运维工程师","武汉","测试完成","互联网/科技","https://hr.xiaomi.com/campus","2027届8月10日开启；网申截止口径 2026-12-31（校招日历另有9-30批次节点）","2026-12-31"),
("107","蚂蚁集团","AI测试开发工程师","杭州/上海","未标注","互联网/科技","https://talent.antgroup.com/campus/home","2027届8月10日开启；网申/笔试排期至 2026-10-29；技术岗占80%，含安全/AI安全","2026-10-29"),
("49","千问（阿里巴巴）","AI安全技术工程师","杭州","未标注","互联网/科技","https://campus-talent.alibaba.com","2027届8月5日开启；集团统一入口，通义千问/阿里云均从此选岗；每业务集团1次机会",""),
("36","快手","安全工程师（北京）、运维工程师实习","北京","未回/无offer","互联网/科技","https://campus.kuaishou.cn","2027校招8月12日开启；滚动招满即止；一次限投1岗",""),
("55","小红书","网络工程师IT、基础技术","上海/北京","未标注","互联网/科技","https://job.xiaohongshu.com/campus","2027校招9月8日开启；一次最多投5岗并自主排序",""),
("56","得物","数据安全工程师","上海","9.02 投递","互联网/科技","https://campus.dewu.com","2027届8月10日开启；技术岗笔试排到11月1日，Offer 11月起发",""),
("40/125","滴滴","网络工程师；另投安全运营实习生","北京","未回/无offer","互联网/科技","https://campus.didiglobal.com","2027届8月13日开启；全渠道合计3次投递机会；含安全技术类；台账125号为安全运营实习生",""),
("39","SHEIN 希音","IT运维实习生","南京","未标注","互联网/科技","https://app.mokahr.com/campus_apply/shein/2932","2027秋招9月4日开启；最多投3岗；Moka 校招门户",""),
("42","Shopee（深圳虾皮）","SRE（运维）工程师","深圳","未回/无offer","互联网/科技","https://app.mokahr.com/su/nykvgs","2027秋招7月28日开启；网申截止 2026-11-30；每人仅1个志愿","2026-11-30"),
("115","携程","SRE 工程师","上海","测评未完成","互联网/科技","https://campus.ctrip.com","2027届8月26日开启，招满即止；秋招每人仅1次投递机会",""),
("43","腾讯音乐 TME","业务运维","深圳/北京","未标注","互联网/科技","https://join.tencentmusic.com/campus","2027校招8月14日开启；每人只可投1个职位",""),
("44/86","联想","运维开发工程师（天津）、IT运维工程师（深圳）","天津、深圳","深圳岗未回/无offer","互联网/科技","https://talent.lenovo.com.cn/","2027届网申 8月5日—11月13日，招满随时关停；内推码 2027XZLMZQY","2026-11-13"),
("78/118","vivo","网络工程师","东莞","未标注","互联网/科技","https://hr-campus.vivo.com/","⚠️ 2027届网申已于 2026-09-15 12:00 截止（台账118号为重复投递记录），只能看进度，等补录/春招","2026-09-15"),
("23","智元机器人（AGIBOT）","网络安全工程师、安全运维工程师","上海","未标注","互联网/科技","https://agirobot.jobs.feishu.cn/s/y8YSmRPj5Xk","2027届校招已开；技术族含安全工程类、技术运维类","2026-11-29"),
("10/19","恒生电子","运维工程师","杭州","已进笔试","互联网/科技","https://campus.hundsun.com","2027届网申 8月13日—10月23日；首轮笔试9月23日、面试10月10日起","2026-10-23"),
("106","金蝶","安全工程（AI方向）","深圳","未标注","互联网/科技","https://app.mokahr.com/campus-recruitment/kingdeehr/166565?locale=zh-CN","2027届网申 2026-09-04—11-04","2026-11-04"),
("68","帆软","项目运维经理","无锡","未标注","互联网/科技","https://join.fanruan.com/campus","提前批8月已结束，正式批进行中；进度在「帆软招聘」公众号查询",""),
("41","合合信息","运维工程师","上海","未标注","互联网/科技","https://intsig.zhiye.com/campus/jobs","2027届7月底开启；投递截止 2026-10-31","2026-10-31"),
("53","满帮集团","安全工程师（非内推）","南京/贵阳","未标注","互联网/科技","http://campus.fulltruckalliance.com/","2027届8月27日开启；含安全/技术方向",""),
("54","科锐国际","软件测试工程师","上海等","未标注","互联网/科技","https://campus.careerintlinc.com","2027届9月7日起网申；最多投5个岗位",""),
("80","数字政通","项目实施工程师（满三个月可转正包住）","武汉/长沙","未标注","互联网/科技","https://egova.zhiye.com/Campus","2027届9月12日开启；笔试10月中下旬—11月底",""),
("89","浙江保融科技","测试工程师","杭州","未标注","互联网/科技","https://campus.fingard.com","2027届9月2日启动；网申9—10月，笔试前一天关闭通道",""),
("38","科大讯飞","计算网络技术工程师","合肥","未标注","互联网/科技","https://campus.iflytek.com/","2027届8月中旬开启；最多投2个岗位；投递后需先做测评",""),
("76","好未来（学而思）","SRE 工程师","北京","未标注","互联网/科技","https://job.xueersi.cn/","2027届秋招8月27日发布；教研/产研/运营等方向",""),
("25","高知特 Cognizant","信息技术岗（10月份岗位）","上海/大连","未标注","互联网/科技","https://careers.cognizant.com/studentandinterns/cn/zh","中国区学生/应届生入口长期开放，按岗位+城市搜索投递",""),
("2","上海甄汇（汇联易）","交付业务顾问","武汉、广州","学长内推","互联网/科技","https://app.mokahr.com/campus_apply/huilianyi/38709","2027届9月初开启；流程含中文笔试 + AI 英文测验",""),
("123","哔哩哔哩（台账写「bibi」）","服务器运维工程师、安全工程师","上海","未标注","互联网/科技","https://jobs.bilibili.com/campus/positions","2027届秋招8月3日开启；安全工程师岗官网职位页标注网申截止 2026-12-31；每人限投2个志愿，初筛前可撤回重投补内推码","2026-12-31"),
# ---- 游戏 ----
("32","网易（互娱）","游戏安全运营","广州","未回/无offer","游戏","https://game.campus.163.com","2027届9月初开启；可投2个志愿；集团总入口 campus.163.com、雷火 leihuo.163.com/campus",""),
("35","米哈游","游戏运维工程师","上海","未回/无offer","游戏","https://jobs.mihoyo.com/#/campus/position","2027届网申截止 2026-10-31；应届生仅能投1个职位","2026-10-31"),
("51","库洛游戏","游戏测试工程师","广州/上海","未回/无offer","游戏","https://kurogame.jobs.feishu.cn/campus","2027秋招8月26日开启；飞书招聘门户",""),
("108","巨人网络","游戏测试工程师","上海","未标注","游戏","https://hr.ztgame.com/campus","2027届8月中旬开启；最多投2个职位，提交后不可改岗",""),
("90","FUNPLUS 趣加","测试工程师","北京/上海/成都/广州","已约笔试并完成","游戏","https://campus.funplus.com.cn","2027届9月初公布；每人3次投递机会（3个志愿）",""),
("12","沐瞳科技","平台运维工程师（AI向）","上海","未标注","游戏","https://moonton.jobs.feishu.cn/campus","2027届8月中旬开启；投递截止约 2026-10-11","2026-10-11"),
("27","多益网络","运维工程师","武汉","测试未完成（没找到入口）","游戏","https://xz.duoyi.com","2027届7月起滚动放岗，招满即止；校招独立站（社招为 sz.duoyi.com）",""),
("29","途游游戏","运维工程师、安全工程师","北京/上海","未回/无offer","游戏","https://app.mokahr.com/campus_apply/tuyoogame/146219","2027届8月20日开启，滚动招满即止；可同时投2个岗位",""),
("4","星辉游戏","运维工程师","广州","未标注","游戏","https://rastargame.jobs.feishu.cn/066491","2027届8月5日开启，招满即止；技术类明确含运维工程师",""),
# ---- 网络安全 / 通信设备 ----
("17","海康威视","网络安全工程师","杭州","测试完成","网络安全/通信","https://campushr.hikvision.com","2027校招已开，滚动招满即止；最多2个志愿",""),
("101","新华三 H3C","测试工程师","杭州/北京","未标注","网络安全/通信","https://career.h3c.com/campus/jobs","2027届8月10日开启，招满即止；笔试8-10月、面试8-11月",""),
("71","锐捷网络","安全研发工程师-防火墙","成都","未回/无offer（非内推）","网络安全/通信","https://www.ruijie.com.cn/campus-recruiting/","27届秋招已开；部分高校公告截止约 2026-11-27；最多2个志愿","2026-11-27"),
("103","绿盟科技","安全工程师","昆明","未标注","网络安全/通信","https://app.mokahr.com/campus_apply/nsfocus/29118#/","网申7月28日—11月中旬；笔试8月下旬起、面试9月上旬起","2026-11-15"),
("74","奇安信","安全工程师（安全运营）","北京","未标注","网络安全/通信","https://campus.qianxin.com/","秋招9月14日开启，招满即止（第三方汇总约 2026-11-14 截止）；每人2个志愿","2026-11-14"),
("30","迪普科技 DPtech","网络安全工程师","杭州","未标注","网络安全/通信","https://zhaopin.dptech.com","2027届「D计划」已开；西南交大公告截止 2026-11-30","2026-11-30"),
("3","天地和兴","项目交付工程师","武汉","未标注","网络安全/通信","https://tdhx.zhiye.com/campus/jobs","「和苗计划」9月11日起；截止约 2026-11-04；工控安全方向","2026-11-04"),
("84","宇视科技 Uniview","平台运维工程师","成都","测试未完成","网络安全/通信","https://talent.uniview.com/wt/uniview/web/index/campus","网申/内推9-10月，笔试面试10月下旬起；每人只能投1个岗位",""),
("52","TP-Link 联洲","系统测试工程师","成都","未标注","网络安全/通信","https://join.tplinkglobal.com/campus","8月14日开启网申，招满即止；秋招每人仅可投1个岗位",""),
("93","爱立信（中国）","无线网络优化工程师（南京）、无线网络工程师（重庆）","南京、重庆","未回/无offer","网络安全/通信","https://www.moseeker.com/site/156","2027校招已开；官方指定 PC 端网申平台；每人最多投2个岗位",""),
("31","卓驭科技","网络安全工程师","深圳","测试未完成","网络安全/通信","https://we.zyt.com/campus","7月15日开放投递、招满即止；27届校招含信息安全类岗位",""),
("109","卓望","运维工程师","深圳","进笔试且笔试通过","网络安全/通信","https://aspire.zhiye.com/Campus","2027校招9月初发布；含安全开发、运维工程师岗",""),
("110","华讯（华讯网络）","技术支持工程师（重庆）、技术服务工程师（上海）","重庆、上海","未标注","网络安全/通信","http://careers.eccom.com.cn/CN/IS/Careers/About/index.asp","2027届目前以实习生招聘形式开放（技术服务/安全/技术支持），实习优异可优先校招录用",""),
("61","通号低空","通信工程师","北京/南京/珠海","无回应/无offer","网络安全/通信","https://thdk.zhiye.com","2027届校招已开；硕士22-28万、博士30-40万，择优解决北京户口",""),
("62","通号工程局集团","通信项目技术岗","—","未标注","网络安全/通信","http://2027.yingjiesheng.com/crsc/pc/PCplan.html","2027届9月11日全面启动；笔试由各所属单位自行组织，无统一截止日",""),
("63","通号工程电气化局","项目技术","郑州","未标注","网络安全/通信","http://2027.yingjiesheng.com/crsc/","走中国通号统一校招专区；未设独立校招域名，需在专区筛选所属单位",""),
("64","卡斯柯信号 CASCO","系统安全工程师","上海","未标注","网络安全/通信","https://casco.zhiye.com/campus","2027年度校招已开；上海为主",""),
("65","北京现代通号工程咨询","信息系统工程师","北京","未标注","网络安全/通信","http://2027.yingjiesheng.com/crsc/","走中国通号统一校招专区；无独立校招网站",""),
("126","中兴通讯","网络技术研发工程师","南京","未标注","网络安全/通信","https://job.zte.com.cn","2027届校招8月31日起网申，无截止、招满即止（武大就业网9月简章）；PC端官网或 Moka 投递，测评仅1次机会；武大就业网内推链接 app.mokahr.com/su/vmqVn",""),
# ---- 国企 / 央企 / 金融 / 能源 ----
("7/104","中国电信","云网运维（万州）、无线网络工程师（重庆）、无线网络优化（南京）","万州、重庆、南京","未标注","国企/金融/能源","https://job.chinatelecom.com.cn/","2027年度8月24日起网申；每人每批次可填3家分子公司，各省截止日不同",""),
("111","中国通信服务广东公司","通信设计工程师","广州","未标注","国企/金融/能源","https://iter.stongyw.cn/web/school/job/index.html","2027届9月中下旬启动；每人最多申请3个职位",""),
("45","中国工商银行","应用运维SRE工程师（北京）、信息安全岗（杭州）","北京、杭州","未标注","国企/金融/能源","https://job.icbc.com.cn","2027届9月初起；总行本部报名截止 2026-10-08，各分行截止不同；笔试预计10月下旬","2026-10-08"),
("57","国家开发银行","未知岗位","—","测试完成","国企/金融/能源","https://cdb2027.zhaopin.com","2027届报名 2026-09-12 12:00 — 10-07 24:00；可选1-2家单位；笔试11月初","2026-10-07"),
("67/117","中国人寿","信息技术岗；另投数字支持部（河南）、科技岗（成都）","—","未标注","国企/金融/能源","https://www.chinalife.com.cn/chinalife/zhaopin","2027年度校招已开；总部岗截止 2026-10-15，下辖机构最晚 11-15；最多3个平行志愿","2026-10-15"),
("69","中金公司","运维实习生","香港","未标注","国企/金融/能源","https://cicc.zhiye.com","2027届网申 2026-09-08 — 10-28；2个平行志愿","2026-10-28"),
("92","平安银行","运维管理师/应用运维管理师（深圳）、安全管理工程师（上海）","深圳、上海","未标注","国企/金融/能源","https://campus.pingan.com/pab","2027届网申 8月10日—11月06日；测评笔试8—11月分批","2026-11-06"),
("33","招银网络科技","运营研发工程师","深圳","未标注","国企/金融/能源","https://cmbnt.cmbchina.com","2027秋招7月底启动；官网进「校园招聘」页注册投递；岗位含运维研发",""),
("79","中国石油","数智化与信息工程（青海、广东）","青海、广东","未标注","国企/金融/能源","https://zhaopin.cnpc.com.cn","2027届9月9日开启，投简历截止 2026-10-15 23:59；通用能力考试11月中上旬","2026-10-15"),
("46/47","中化数智科技","网络安全工程师、基础设施工程师","雄安新区","测试完成","国企/金融/能源","https://sinochem.hotjob.cn","「图灵计划」第十期，网申 2026-09-15 — 12-31；投递时招聘机构选中化数智","2026-12-31"),
("48","中国化工橡胶","信息技术工程师","河南焦作","未标注","国企/金融/能源","https://sinochem.hotjob.cn","「橡新力」管培生计划，网申截止 2026-12-31；焦作岗位多挂下属风神轮胎","2026-12-31"),
("58","中国中车","网络安全工程师（长春）、计算机工程师（大同）","长春、大同","未标注","国企/金融/能源","https://crrc.hotjob.cn","2027届9月上旬启动（3000+ offer）；限投2家子公司、每家1岗",""),
("26","东风汽车","信息安全（测试完成）、云运维工程师（社招）","武汉","信息安全岗测试完成","国企/金融/能源","https://www.dfmc.com.cn","2027届9月上旬启动；官网「人才招聘→校园招聘」；最多投5家单位",""),
("21","中建安装集团","安全管理岗","南京、广州","进第一轮，测试完成","国企/金融/能源","https://hcm.pub/cbm4p","2027届「信·新青年」9月中下旬发布；需参加中建集团统一线上测评；简章有效期至 11-30","2026-11-30"),
("102","陕煤集团","信息维护岗","西安","未标注","国企/金融/能源","https://webhr.shccig.com/webhrN2-zp","2027年度9月16日启动（招3000余人）；报名截止 2026-10-31；限报3个单位","2026-10-31"),
("24","北方矿业","信息技术岗","北京","未标注","国企/金融/能源","https://bfky.iguopin.com","2027届已开（7月先启动实习生计划）；岗位以北京总部为主，面向硕博",""),
("82","中国融通医疗健康集团","信息运维岗","临夏","未标注","国企/金融/能源","https://job.crtc-hr.com/sld/campus","2027届报名截止 2026-10-30 17:00；平台内搜索具体医院后选岗，限投1个岗位","2026-10-30"),
("66","佳木斯电机（哈电佳电）","信息技术岗","佳木斯","未标注","国企/金融/能源","https://www.jemlc.com/cpyc/xyzp.htm","2027届招聘进行中；官网校招页以邮箱投递为主 jd_zhaopin123@163.com",""),
("59","重庆医药集团（广阔医药）","信息管理员","重庆","未标注","国企/金融/能源","https://genertec.zhiye.com","属中国通用技术集团，岗位统一挂在通用技术校招平台，需站内按单位筛选",""),
("60","贵州省医药集团（和平医药）","计算机管理员","贵州","未标注","国企/金融/能源","https://genertec.zhiye.com","同属通用技术集团体系，岗位在通用技术校招平台内，无独立校招站",""),
("120","中邮消费金融（台账写「中油消费金融」）","信息安全（IT技术类）","广州","未标注","国企/金融/能源","https://is35svcbne.jobs.feishu.cn/youcash/","⚠️ 高度疑为「中邮消费金融」笔误（邮储银行旗下，请核对）。2027届秋招IT技术类含信息安全岗；飞书网申+公众号【中邮消费金融招聘】；高校就业网帖子有效期至 2026-10-07，官方截止以公众号为准",""),
("121","中国铁塔","算力网络","浙江","未标注","国企/金融/能源","https://zhaopin.chinatowercom.cn","官方唯一网申入口；9/26 查证 27 届正式批公告尚未发布，往年节奏 10 月中旬网申、11 月中旬统一笔试；无内推码，警惕收费「保录取」",""),
("122","中广核数字科技","运维岗","深圳","未标注","国企/金融/能源","https://www.cgnpc.com.cn/","走中广核集团统一校招（9月4日起投递，网申至10月底，公众号「中广核校园招聘」）；数字科技板块含系统运维/网络安全岗，另有国聘 cgnpc.iguopin.com 入口；可填2个志愿公司","2026-10-31"),
# ---- 制造 / 消费电子 / 物流 / 医药 ----
("20/99","汇川技术","运维工程师、IT安全/基础设施工程师","苏州/深圳等","未标注","制造/消费电子","https://recruit.inovance.com","2027届首批岗位7月已上线、全球启动；流程网申→测评→面试（3轮）→offer",""),
("14","长虹控股","系统运维","四川","未标注","制造/消费电子","https://zhaopin.changhong.com","2027届9月16日起网申，川渝线下宣讲已开跑；集团+子公司统一入口",""),
("94/95","海信","软件运维工程师（网络，青岛）","青岛","未标注","制造/消费电子","https://jobs.hisense.com","「信动力计划」7月31日开放；进「校园招聘」版块投递",""),
("8","奔图科技（Pantum）","技术支持/网络工程类","珠海、合肥","测试完成","制造/消费电子","https://pantum.zhiye.com/Campus","2027届秋招已开，招满即止；每人最多申1岗+第二志愿；技术支持类含网络工程/系统管理",""),
("18","安克创新 Anker","运维工程师","深圳","未标注","制造/消费电子","https://career.anker.com.cn/universities/recruitment/","2027届8月18日启动；每人最多申3岗，未公布统一截止日",""),
("34","影石 Insta360","桌面运维工程师","深圳","未标注","制造/消费电子","https://www.insta360.com/cn/jobs","2027届秋招已开；网申截止 2026-10-31 19:00；另有「X计划」SP Offer 通道","2026-10-31"),
("73","韶音 Shokz","IT战略管培生（网络系统信安方向）","深圳","未标注","制造/消费电子","https://hr.shokz.com.cn","2027届秋招已开（提前批已先行）；岗位含IT类，内推码可加速",""),
("91/105","正浩 EcoFlow","SRE运维工程师","深圳","未标注","制造/消费电子","https://jobs.ecoflow.com/602892","⚠️ 2027届网申约 9/1—9/29（部分渠道写10/1），即将截止，尽快投递","2026-09-29"),
("87","精智达","AI网络工程师","深圳","未标注","制造/消费电子","https://app.mokahr.com/campus-recruitment/seichitech/140888?locale=zh-CN","2027届9月起宣讲；半导体测试设备方向；部分高校公告过期时间 2026-11-30","2026-11-30"),
("85","思朗科技","运维开发工程师","天津","未标注","制造/消费电子","https://smartlogictech.jobs.feishu.cn/xiaozhao/m/?spread=82A5QW5","2027校招已开；集成电路/算法/软件/硬件类",""),
("50","凌云光技术","运维测试工程师","苏州","未标注","制造/消费电子","https://app.mokahr.com/campus-recruitment/lusterinc/44882","2027届校招已开；机器视觉+光通信方向",""),
("11","湖北亿纬动力（亿纬锂能）","研发、制造、运营、营销等","荆门/惠州","未标注","制造/消费电子","https://zhaopin.evebattery.com","2027届全球校招已开；荆门与惠州基地岗位均在此选；滚动筛选建议早投",""),
("13","亿纬锂能（社招）","网络工程师","惠州","社招","制造/消费电子","https://zhaopin.evebattery.com","台账标「社招」，校招官网同站，社招请切到社招频道",""),
("100","双胞胎集团","IT工程师","广州","未回/无offer","制造/消费电子","https://www.sbtjt.com/xyzp.jhtml","2027届校招已开；官网「加入双胞胎→校园招聘」，流程含AI面试",""),
("28","豪迈集团","运维工程师","山东","未回/无offer，测试完成","制造/消费电子","https://himile.zhiye.com","「深蓝计划」提前批6月起，秋招9月启动；岗位集中在山东高密",""),
("112","奥马冰箱","系统实施工程师","中山","未标注","制造/消费电子","https://homa-hr.zhiye.com/","2027届提前批网申 7/26—9/24，正式批继续；信息技术类含IT运维方向",""),
("113","碧桂园","软件测试岗","佛山/广东","未标注","制造/消费电子","https://zhaopin.bgy.com.cn/campus","2027届「碧业生」已开；物业板块走 bgyfw.com",""),
("114","普利特（台账写「普列特」）","ERP-F&O 运维","上海","未标注","制造/消费电子","https://pret.zhiye.com/campus","2027届全球秋招8月24日开启；ERP-F&O运维与开发工程师(.NET & X++)在上海青浦",""),
("97","泸州老窖（台账写「老窑」）","信息技术","泸州","未标注","制造/消费电子","https://job.lzlj.com/campus/jobs","2027届9月16日公告；网申截止 2026-11-06 17:00，招满即止，限投1主岗+1调剂","2026-11-06"),
("70","极兔快递 J&T","网络管理管培生、信息安全管培生","上海","未标注","制造/消费电子","https://jtexpress.jobs.feishu.cn/478610","2027届「繁星计划」9月3日网申开启；最多投2个岗位",""),
("81","顺丰（顺丰航空）","运维开发工程师（深圳）、信息安全运营工程师（武汉）","深圳、武汉","未标注","制造/消费电子","https://campus.sf-express.com/#/homePage","2027届校招已开；科技岗深圳/武汉/成都，航空与运营岗见站内项目列表",""),
("98","华海药业","设备运维工程师","台州","未标注","制造/消费电子","","⚠️ 未确认：官方仅公布邮箱投递 campus@huahaipharm.com（主题：期望工作地点-应聘岗位-姓名-学校-专业-学历-2027）",""),
("116","美的集团","应用服务工程师","未标注","未标注","制造/消费电子","https://careers.midea.com","2027届校招已开（毕业时间2026/1—2027/12）；简历筛选与测评至11月初、面试至11月底；投递不限次数、面试前可切换岗位城市；内推码 M772H4 出自华中师大就业网简章",""),
("119","荣耀","AI安全工程师","未标注","未标注","制造/消费电子","https://www.honor.com/cn/career/","🔴 2027届本硕简历投递截止 2026-09-30 24:00（多所高校就业网确认），只剩几天尽快投；8大类含「流程IT与质量运营」；研发类流程机考→业务面→测评→综合面","2026-09-30"),
("124","OPPO（台账写「oppo」）","运维工程师实习、安全算法工程师实习","未标注","未标注","制造/消费电子","https://careers.oppo.com/university/oppo/campus","2027届网申 2026-07-15—11-30（牛客企业页口径），招满即止；实习与秋招同入口；流程含测评，部分岗笔试/AI面试","2026-11-30"),
# ---- 待人工核对 ----
("1","欣达旺","—","广州、深圳","内推（9.4大群）；测试完成，未完成第五部分","待核对","","⚠️ 未确认：未搜到该校招官网。工商有「深圳市欣达旺科技」（小微企业，无校招站）；高度怀疑是「欣旺达 Sunwoda」笔误 → https://sunwodacampus.zhiye.com ，请核对公司全称",""),
("9","德发电子信息","网络工程师、运维工程师","武汉","未标注","待核对","https://www.defae.com","⚠️ 未确认校招门户：公司真实存在（系统集成/IT运维），主要通过高校双选会、湖北高校就业网络联盟发布岗位，建议走院校就业网核实",""),
("83","舒尔电子（Shure 苏州）","算法测试工程师","苏州（台账写临夏）","未标注","待核对","","⚠️ 未确认校招门户：2027届网申约9月8日起、11月上旬截止；官方只给邮箱 shens@shure.com / luza@shure.com",""),
("96","飞速（飞速创新 FS）","技术培训生","武汉","未标注","待核对","https://cn.fs.com","⚠️ 未确认校招门户：武汉分公司确有技术培训生岗位，公开渠道只找到邮箱 resume@feisu.com；建议从官网招聘入口确认",""),
]

APPENDIX = [
("深圳燃气","信息技术岗（含网络安全）","深圳","https://szgas.zhiye.com/campus","2027届9月14日启动；深圳总部岗以硕士为主，外地子公司本科可投",""),
("特区建工集团","工程管理/信息技术类","深圳","https://szcg.zhaopin.com/","2027届9月11日起发布，招约120人；14家二级企业统一选岗",""),
("中信银行信用卡中心","信息技术类","深圳","https://creditcard.ecitic.com/zhaopin","2027届简历接收暂定截止 2026-10-18 24:00；与中信银行总行平台分开投递","2026-10-18"),
("中国移动湖北公司","信息技术类","湖北","https://job.10086.cn","2027届投简历截止 2026-10-16 24:00；限投2个志愿","2026-10-16"),
("贝泰妮集团","AI产品架构师/信息技术类","上海、昆明、北京","https://app.mokahr.com/campus-recruitment/botanee/95426","2027届校招已开；6大岗位类型","2026-10-31"),
("华虹集团","半导体/信息技术类","上海、无锡、成都","https://app.mokahr.com/campus-recruitment/huahong/78009","2027届校招已开，招募千人以上；另有 campus.hua-hong.com / campus.hhgrace.com 两个入口未验证","2026-10-24"),
("深信服","安全/攻防研究/X-STAR","深圳","https://hr.sangfor.com/","2027届网申 8月20日—11月30日；无笔试无测评；秋招每人仅可投1个岗位","2026-11-30"),
]

EVENTS = [
("5","2026-09-16 武汉大学招聘会","线下招聘会（非公司）"),
("6","2026-09-17 学校招聘会","线下招聘会（非公司）"),
("15","2026-09-22 13:30 电信荆州","中国电信荆州分公司线下场次"),
("16","2026-09-17 学校招聘会（理工科专场）","线下招聘会（非公司）"),
]

TODAY = datetime.date(2026, 9, 26)

def days_left(dl):
    if not dl:
        return None
    y, m, dd = [int(x) for x in dl.split("-")]
    return (datetime.date(y, m, dd) - TODAY).days

# ---------------- Markdown ----------------
def build_md():
    L = []
    L.append("# 已投递公司 · 校园招聘官网清单\n")
    L.append("> 最后更新：**2026-09-26**　|　数据来源：`WPS云盘/工作计划完成统计表1.xlsx` →「五月」sheet 投递台账　|　共 **{}** 家公司/机构\n".format(len(DATA)))
    L.append("> 台账中另有 4 条线下招聘会记录（见文末），非公司，不计入统计。\n")

    # 近期截止
    dls = [(d, days_left(d[8])) for d in DATA if d[8]]
    dls = [x for x in dls if x[1] is not None]
    dls.sort(key=lambda x: x[1])
    L.append("\n## ⏰ 已确认网申截止日（按剩余天数排序）\n")
    L.append("| 剩余 | 截止日 | 公司 | 校招官网 |")
    L.append("|---|---|---|---|")
    for d, n in dls:
        flag = "🔴 已截止" if n < 0 else ("🔴 紧急" if n <= 7 else ("🟡 本周" if n <= 14 else "⚪ 常规"))
        cnt = f"{n} 天" if n >= 0 else f"已过 {-n} 天"
        L.append(f"| {flag} {cnt} | {d[8]} | {d[1]} | [打开]({d[6]}) |")

    cats = ["互联网/科技", "游戏", "网络安全/通信", "国企/金融/能源", "制造/消费电子", "待核对"]
    for c in cats:
        rows = [d for d in DATA if d[5] == c]
        L.append(f"\n## {c}（{len(rows)} 家）\n")
        L.append("| 台账# | 公司 | 投递岗位 | 地点 | 台账状态 | 校招官网 | 备注 |")
        L.append("|---|---|---|---|---|---|---|")
        for d in rows:
            link = f"[打开]({d[6]})" if d[6] else "—"
            L.append(f"| {d[0]} | **{d[1]}** | {d[2]} | {d[3]} | {d[4]} | {link} | {d[7]} |")

    L.append("\n## 📎 附录：邮件推荐的公司（未进台账，网址备查）\n")
    L.append("| 公司 | 岗位 | 地点 | 校招官网 | 备注 |")
    L.append("|---|---|---|---|---|")
    for a in APPENDIX:
        L.append(f"| **{a[0]}** | {a[1]} | {a[2]} | [打开]({a[3]}) | {a[4]} |")

    L.append("\n## 📅 台账中的线下招聘会记录\n")
    for e in EVENTS:
        L.append(f"- 序号 {e[0]}：{e[1]} —— {e[2]}")

    L.append("\n## ⚠️ 需要你人工核对的 5 家\n")
    for d in DATA:
        if d[5] == "待核对":
            L.append(f"- **{d[1]}**（台账序号 {d[0]}）：{d[7]}")

    L.append("\n---\n\n## 更新日志\n")
    L.append("- 2026-09-25　首次生成，从台账解析 115 条记录 → 去重得到 {} 家公司/机构，联网核实校招官网，{} 家已确认、5 家待人工核对。".format(len(DATA), len(DATA) - 5))
    L.append("- 2026-09-26　台账更新到序号 131（新增 9/26 凌晨记录）：新增 8 家（哔哩哔哩、中兴、中邮消费金融、中国铁塔、中广核数字科技、美的、荣耀、OPPO），全部联网核实校招官网；vivo/中国人寿/滴滴 为重复投递，合并进原条目。")
    return "\n".join(L)

# ---------------- HTML ----------------
def build_html():
    items = []
    for i, d in enumerate(DATA):
        n = days_left(d[8])
        if n is None:
            urg, dl_txt = "none", "未公布/招满即止"
        elif n < 0:
            urg, dl_txt = "over", f"{d[8]}（已截止）"
        elif n <= 7:
            urg, dl_txt = "hot", f"{d[8]}（剩 {n} 天）"
        elif n <= 14:
            urg, dl_txt = "warn", f"{d[8]}（剩 {n} 天）"
        else:
            urg, dl_txt = "ok", f"{d[8]}（剩 {n} 天）"
        items.append({
            "id": i, "seq": d[0], "name": d[1], "role": d[2], "loc": d[3],
            "status": d[4], "cat": d[5], "url": d[6], "note": d[7],
            "dl": d[8], "urg": urg, "dlTxt": dl_txt,
        })
    appx = [{"name": a[0], "role": a[1], "loc": a[2], "url": a[3], "note": a[4]} for a in APPENDIX]

    import json
    js_data = json.dumps(items, ensure_ascii=False)
    js_appx = json.dumps(appx, ensure_ascii=False)

    n_all = len(items)
    n_ok = len([x for x in items if x["url"]])
    n_hot = len([x for x in items if x["urg"] == "hot"])
    n_over = len([x for x in items if x["urg"] == "over"])

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>已投递公司 · 校园招聘官网看板</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#f5f6f8;color:#1f2329;padding:24px}}
  .wrap{{max-width:1280px;margin:0 auto}}
  header{{background:#fff;border:1px solid #e5e6eb;border-radius:12px;padding:22px 26px;margin-bottom:18px}}
  h1{{font-size:21px;font-weight:600;margin-bottom:6px}}
  .sub{{font-size:13px;color:#86909c;line-height:1.7}}
  .stats{{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}}
  .stat{{flex:1;min-width:130px;background:#f7f8fa;border:1px solid #e5e6eb;border-radius:10px;padding:14px 16px}}
  .stat b{{display:block;font-size:24px;font-weight:600;line-height:1.2}}
  .stat span{{font-size:12px;color:#86909c}}
  .toolbar{{background:#fff;border:1px solid #e5e6eb;border-radius:12px;padding:14px 18px;margin-bottom:18px;display:flex;gap:10px;flex-wrap:wrap;align-items:center}}
  input[type=text]{{flex:1;min-width:200px;padding:9px 13px;border:1px solid #d9dce0;border-radius:8px;font-size:14px;outline:none}}
  input[type=text]:focus{{border-color:#3b6ef5}}
  .chip{{padding:7px 14px;border:1px solid #d9dce0;border-radius:20px;font-size:13px;cursor:pointer;background:#fff;user-select:none}}
  .chip.on{{background:#3b6ef5;color:#fff;border-color:#3b6ef5}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:14px}}
  .card{{background:#fff;border:1px solid #e5e6eb;border-radius:12px;padding:16px 18px;display:flex;flex-direction:column;gap:8px;border-left:4px solid #c9cdd4}}
  .card.hot{{border-left-color:#e54545;background:#fffafa}}
  .card.warn{{border-left-color:#ff9a2e}}
  .card.over{{border-left-color:#86909c;opacity:.72}}
  .card.ok{{border-left-color:#23a55a}}
  .card h3{{font-size:15px;font-weight:600;display:flex;align-items:center;gap:8px}}
  .seq{{font-size:11px;color:#86909c;background:#f2f3f5;border-radius:4px;padding:2px 6px;font-weight:400}}
  .role{{font-size:13px;color:#4e5969;line-height:1.5}}
  .meta{{font-size:12px;color:#86909c;display:flex;gap:12px;flex-wrap:wrap}}
  .note{{font-size:12px;color:#4e5969;background:#f7f8fa;border-radius:6px;padding:8px 10px;line-height:1.6}}
  .dl{{font-size:12px;font-weight:600;padding:4px 9px;border-radius:6px;display:inline-block}}
  .dl.hot{{background:#ffece8;color:#e54545}}
  .dl.warn{{background:#fff7e8;color:#d97706}}
  .dl.ok{{background:#e8f7ee;color:#1a8a4a}}
  .dl.over{{background:#f2f3f5;color:#86909c}}
  .dl.none{{background:#f2f3f5;color:#86909c}}
  a.btn{{display:block;text-align:center;margin-top:2px;padding:9px;background:#3b6ef5;color:#fff;border-radius:8px;text-decoration:none;font-size:13px;font-weight:500}}
  a.btn:hover{{background:#2f5ccc}}
  a.btn.na{{background:#f2f3f5;color:#a9aeb8;pointer-events:none}}
  h2.sec{{font-size:16px;font-weight:600;margin:26px 0 12px;padding-left:10px;border-left:4px solid #3b6ef5}}
  .empty{{padding:40px;text-align:center;color:#86909c;font-size:14px}}
  footer{{margin-top:26px;font-size:12px;color:#a9aeb8;text-align:center;line-height:1.8}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>已投递公司 · 校园招聘官网看板</h1>
    <div class="sub">
      数据来源：<b>WPS云盘 / 工作计划完成统计表1.xlsx</b> →「五月」sheet 投递台账（131 条记录，去重后 {n_all} 家）<br>
      校招官网均于 2026-09-26 联网核实　|　最后更新：<b>2026-09-26</b>
    </div>
    <div class="stats">
      <div class="stat"><b>{n_all}</b><span>公司总数</span></div>
      <div class="stat"><b style="color:#23a55a">{n_ok}</b><span>官网已确认</span></div>
      <div class="stat"><b style="color:#e54545">{n_hot}</b><span>7天内截止</span></div>
      <div class="stat"><b style="color:#86909c">{n_over}</b><span>已截止</span></div>
    </div>
  </header>

  <div class="toolbar">
    <input type="text" id="q" placeholder="搜索公司名 / 岗位 / 地点…">
    <span class="chip on" data-f="all">全部</span>
    <span class="chip" data-f="hot">7天内截止</span>
    <span class="chip" data-f="互联网/科技">互联网/科技</span>
    <span class="chip" data-f="游戏">游戏</span>
    <span class="chip" data-f="网络安全/通信">网络安全/通信</span>
    <span class="chip" data-f="国企/金融/能源">国企/金融/能源</span>
    <span class="chip" data-f="制造/消费电子">制造/消费电子</span>
    <span class="chip" data-f="待核对">待核对</span>
  </div>

  <div class="grid" id="grid"></div>
  <div class="empty" id="empty" style="display:none">没有匹配的公司</div>

  <h2 class="sec">附录：邮件推荐的公司（未进台账）</h2>
  <div class="grid" id="grid2"></div>

  <footer>
    每天自动比对 xlsx 台账，新增公司会自动补充校招官网并追加到本看板与 Markdown 清单<br>
    标记「未确认」的 5 家请人工核对公司全称后再投递
  </footer>
</div>

<script>
const DATA = {js_data};
const APPX = {js_appx};
const grid = document.getElementById('grid');
const grid2 = document.getElementById('grid2');
const empty = document.getElementById('empty');
let filter = 'all', kw = '';

function esc(s){{return (s||'').replace(/[&<>"]/g, c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}})[c]);}}

function card(d){{
  const has = !!d.url;
  return `<div class="card ${{d.urg}}">
    <h3>${{esc(d.name)}}<span class="seq">台账#${{esc(d.seq)}}</span></h3>
    <div class="role">${{esc(d.role)}}</div>
    <div class="meta"><span>📍 ${{esc(d.loc)||'—'}}</span><span>状态：${{esc(d.status)||'—'}}</span></div>
    <div><span class="dl ${{d.urg}}">${{esc(d.dlTxt)}}</span></div>
    <div class="note">${{esc(d.note)}}</div>
    <a class="btn ${{has?'':'na'}}" href="${{has?d.url:'javascript:void(0)'}}" target="_blank" rel="noopener">${{has?'打开校招官网 →':'官网未确认'}}</a>
  </div>`;
}}

function render(){{
  const list = DATA.filter(d=>{{
    const okF = filter==='all' ? true : (filter==='hot' ? d.urg==='hot' : d.cat===filter);
    const s = (d.name+d.role+d.loc+d.note).toLowerCase();
    return okF && (!kw || s.includes(kw));
  }});
  grid.innerHTML = list.map(card).join('');
  empty.style.display = list.length? 'none':'block';
  grid2.innerHTML = APPX.map(a=>`<div class="card">
    <h3>${{esc(a.name)}}</h3>
    <div class="role">${{esc(a.role)}}</div>
    <div class="meta"><span>📍 ${{esc(a.loc)}}</span></div>
    <div class="note">${{esc(a.note)}}</div>
    <a class="btn" href="${{a.url}}" target="_blank" rel="noopener">打开校招官网 →</a>
  </div>`).join('');
}}
document.getElementById('q').addEventListener('input', e=>{{kw=e.target.value.trim().toLowerCase();render();}});
document.querySelectorAll('.chip').forEach(c=>c.addEventListener('click',()=>{{
  document.querySelectorAll('.chip').forEach(x=>x.classList.remove('on'));
  c.classList.add('on'); filter=c.dataset.f; render();
}}));
render();
</script>
</body>
</html>"""

md = build_md()
html = build_html()
with open(os.path.join(OUT_DIR, "已投递公司校招官网.md"), "w", encoding="utf-8") as f:
    f.write(md)
with open(os.path.join(OUT_DIR, "校招官网看板.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("MD lines:", len(md.splitlines()))
print("HTML bytes:", len(html))
print("companies:", len(DATA))
