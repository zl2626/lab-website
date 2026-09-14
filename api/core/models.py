"""课题组网站的数据模型。

内容由 Django Admin 维护，前端在构建时通过 /api/content/ 拉取。
"""

from django.db import models


class Publishable(models.Model):
    """公共字段：是否发布 + 时间戳。"""

    published = models.BooleanField("发布", default=True, help_text="取消勾选后前台不显示")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        abstract = True


class ResearchArea(Publishable):
    """研究方向。"""

    slug = models.SlugField("URL 文件名", max_length=80, unique=True, help_text="英文小写短横线，如 computer-vision")
    title = models.CharField("中文标题", max_length=120)
    title_en = models.CharField("英文标题", max_length=200, blank=True)
    summary = models.TextField("一句话简介", help_text="显示在卡片上")
    icon = models.CharField("图标 emoji", max_length=16, default="🔬")
    keywords = models.JSONField("关键词", default=list, blank=True, help_text='JSON 数组，如 ["目标检测", "图像分割"]')
    order = models.IntegerField("排序", default=99, help_text="数字越小越靠前")
    cover = models.CharField("配图路径", max_length=300, blank=True, help_text="如 /images/research/xxx.jpg")
    body = models.TextField("正文（Markdown）", blank=True)

    class Meta:
        verbose_name = "研究方向"
        verbose_name_plural = "研究方向"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.title


class Member(Publishable):
    """团队成员。"""

    class Role(models.TextChoices):
        """常用身份的默认取值。真正的 role 字段不限制取值，这里只用于提示和默认排序。"""

        PI = "导师", "导师"
        POSTDOC = "博士后", "博士后"
        PHD = "博士生", "博士生"
        MASTER = "硕士生", "硕士生"
        UNDERGRAD = "本科生", "本科生"
        ASSISTANT = "科研助理", "科研助理"
        ALUMNI = "校友", "校友"

    DEFAULT_ROLES = [value for value, _ in Role.choices]

    slug = models.SlugField("URL 文件名", max_length=80, unique=True, help_text="拼音或英文，如 zhang-wei")
    name = models.CharField("姓名", max_length=60)
    name_en = models.CharField("英文名 / 拼音", max_length=120, blank=True)
    role = models.CharField(
        "身份",
        max_length=30,
        blank=True,
        default=Role.PHD,
        help_text="常用取值见输入框建议；也可以自己填，例如「访问学者」「联合培养博士」。"
        "成员页的分组顺序在「站点设置 → 成员页文案 → 身份分组顺序」里调整。",
    )
    title = models.CharField("职称 / 年级", max_length=120, blank=True)
    order = models.IntegerField("组内排序", default=99, help_text="数字越小越靠前")
    photo = models.CharField("照片路径", max_length=300, blank=True, help_text="如 /images/team/xxx.jpg；留空则显示姓名首字头像")
    email = models.EmailField("邮箱", blank=True)
    join_year = models.CharField("加入年份", max_length=10, blank=True)
    now_at = models.CharField(
        "现在在哪 / 毕业去向",
        max_length=160,
        blank=True,
        help_text="例如「某大学 助理教授」「某公司 算法工程师」；校友填写后会在成员页突出显示",
    )
    areas = models.JSONField(
        "所属研究方向",
        default=list,
        blank=True,
        help_text='JSON 数组，填「研究方向」的中文标题，如 ["计算机视觉"]；会在对应方向详情页展示',
    )
    interests = models.JSONField("研究兴趣", default=list, blank=True)
    hobbies = models.JSONField("兴趣爱好", default=list, blank=True)
    research_focus = models.CharField("主要研究方向", max_length=200, blank=True)
    achievement_summary = models.TextField("成果产出", blank=True, help_text="用通俗语言写论文、项目或比赛成果")
    links = models.JSONField(
        "相关链接",
        default=dict,
        blank=True,
        help_text='JSON 对象，支持 homepage / scholar / github / orcid / dblp',
    )
    bio = models.TextField("个人简介（Markdown）", blank=True)

    class Meta:
        verbose_name = "团队成员"
        verbose_name_plural = "团队成员"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.name}（{self.role}）"


class News(Publishable):
    """科研新闻。"""

    slug = models.SlugField("URL 文件名", max_length=120, unique=True, help_text="英文短名，如 cvpr-2026-papers")
    title = models.CharField("标题", max_length=200)
    date = models.DateField("发布日期")
    summary = models.TextField("摘要", blank=True, help_text="列表页显示")
    tags = models.JSONField("标签", default=list, blank=True)
    cover = models.CharField("封面图路径", max_length=300, blank=True)
    pinned = models.BooleanField("置顶", default=False)
    body = models.TextField("正文（Markdown）", blank=True)

    class Meta:
        verbose_name = "科研新闻"
        verbose_name_plural = "科研新闻"
        ordering = ["-date", "-id"]

    def __str__(self) -> str:
        return self.title


class Publication(Publishable):
    """科研成果（论文 / 专利 / 获奖等）。"""

    class Type(models.TextChoices):
        JOURNAL = "期刊论文", "期刊论文"
        CONFERENCE = "会议论文", "会议论文"
        PREPRINT = "预印本", "预印本"
        PATENT = "专利", "专利"
        BOOK = "专著", "专著"
        AWARD = "获奖", "获奖"
        PROJECT = "项目", "项目"

    slug = models.SlugField("URL 文件名", max_length=140, unique=True)
    title = models.CharField("成果标题", max_length=400, help_text="论文标题请用英文原文")
    authors = models.JSONField("作者列表", default=list, blank=True)
    venue = models.CharField("期刊 / 会议全称", max_length=300)
    venue_short = models.CharField("简称", max_length=60, blank=True, help_text="如 CVPR")
    year = models.IntegerField("年份")
    type = models.CharField("成果类型", max_length=20, choices=Type.choices, default=Type.CONFERENCE)
    area = models.CharField(
        "所属研究方向",
        max_length=120,
        blank=True,
        help_text="填「研究方向」的中文标题，才会在该方向详情页关联显示",
    )
    highlight = models.BooleanField("设为精选", default=False, help_text="勾选后会出现在首页「代表性成果」")
    link = models.URLField("原文链接", max_length=500, blank=True)
    pdf = models.URLField("PDF 链接", max_length=500, blank=True)
    code = models.URLField("代码仓库", max_length=500, blank=True)
    abstract = models.TextField("简介", blank=True)

    class Meta:
        verbose_name = "科研成果"
        verbose_name_plural = "科研成果"
        ordering = ["-year", "title"]

    def __str__(self) -> str:
        return f"[{self.year}] {self.title}"


class RobotProject(Publishable):
    """机器人科研平台项目：模型和演示视频用外部链接，避免 serverless 大文件限制。"""
    slug = models.SlugField("项目短名", max_length=120, unique=True)
    name = models.CharField("项目名称", max_length=200)
    summary = models.TextField("项目介绍", blank=True)
    research_focus = models.CharField("研究方向", max_length=200, blank=True)
    model_url = models.URLField("3D 模型地址", max_length=500, blank=True)
    model_format = models.CharField("模型格式", max_length=30, blank=True, help_text="例如 GLB、OBJ、STL")
    demo_url = models.URLField("演示视频地址", max_length=500, blank=True)
    body = models.TextField("详细说明", blank=True)
    order = models.IntegerField("排序", default=99)

    class Meta:
        verbose_name = "机器人项目"
        verbose_name_plural = "科研平台·机器人项目"
        ordering = ["order", "-updated_at", "id"]

    def __str__(self) -> str:
        return self.name


class HomeSlide(Publishable):
    """首页大图轮播的每一屏。

    后台没有配置任何轮播时，首页会回退到「团队合照 + 前两个研究方向」的自动拼接，
    因此老站点不配也能正常显示。
    """

    title = models.CharField("标题", max_length=200)
    title_en = models.CharField("英文副标题", max_length=300, blank=True, help_text="显示在中文标题下方，可留空")
    summary = models.TextField("说明文字", blank=True, help_text="一两句话介绍这一屏在讲什么")
    image = models.CharField("背景图", max_length=500, blank=True, help_text="建议横向大图；留空则使用内置渐变背景")
    link = models.CharField(
        "按钮链接",
        max_length=300,
        blank=True,
        help_text="站内路径（如 /research）或完整 http(s) 地址；留空则不显示按钮",
    )
    link_label = models.CharField("按钮文字", max_length=60, blank=True, help_text="留空则用「了解更多」")
    order = models.IntegerField("排序", default=99, help_text="数字越小越靠前")

    class Meta:
        verbose_name = "首页轮播"
        verbose_name_plural = "首页轮播"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.title


class SiteSetting(models.Model):
    """站点全局设置（单例，只允许保留一条记录）。"""

    name = models.CharField("课题组名称", max_length=120, default="某某实验室")
    name_en = models.CharField("英文名称", max_length=200, blank=True)
    abbr = models.CharField("缩写", max_length=12, default="LAB", help_text="2-5 个字母，显示在 Logo 上")
    tagline = models.CharField("一句话简介", max_length=300, blank=True)
    affiliation = models.CharField("所属单位", max_length=200, blank=True)
    description = models.TextField("搜索引擎简介", blank=True)
    group_photo = models.CharField("首页团队合照", max_length=500, blank=True, help_text="可上传图片或填写公开图片地址；建议横向大图")

    address = models.CharField("通讯地址", max_length=200, blank=True)
    postcode = models.CharField("邮编", max_length=20, blank=True)
    email = models.EmailField("电子邮箱", blank=True)
    phone = models.CharField("联系电话", max_length=60, blank=True)

    openings_enabled = models.BooleanField("显示招生信息", default=True)
    openings_title = models.CharField("招生标题", max_length=200, blank=True)
    openings_text = models.TextField("招生说明", blank=True, help_text="一两句话说明在招什么方向的人")
    openings_details = models.TextField(
        "招生详情（Markdown）",
        blank=True,
        help_text="可写申请材料清单、流程、常见问题；支持 Markdown 列表与链接",
    )
    openings_email = models.EmailField("接收申请邮箱", blank=True)

    nav = models.JSONField(
        "导航菜单",
        default=list,
        blank=True,
        help_text='JSON 数组，如 [{"label": "首页", "href": "/"}]；留空则使用默认菜单',
    )
    social = models.JSONField("页脚链接", default=list, blank=True)
    icp = models.CharField("备案号", max_length=60, blank=True)
    page_copy = models.JSONField("各页面文案", default=dict, blank=True)

    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "站点设置"
        verbose_name_plural = "站点设置"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        # 强制单例
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "SiteSetting":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class MediaFile(models.Model):
    """用户上传的图片，二进制直接存在数据库里。

    这样 serverless 环境不需要可写的文件系统，也不需要额外的对象存储服务。
    """

    name = models.CharField("存储路径", max_length=200, unique=True)
    content_type = models.CharField("MIME 类型", max_length=80, default="image/jpeg")
    size = models.PositiveIntegerField("字节数", default=0)
    width = models.PositiveIntegerField("宽", default=0)
    height = models.PositiveIntegerField("高", default=0)
    data = models.BinaryField("文件内容")
    uploaded_at = models.DateTimeField("上传时间", auto_now_add=True)

    class Meta:
        verbose_name = "图片文件"
        verbose_name_plural = "图片文件"
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return self.name

    @property
    def size_kb(self) -> int:
        return round(self.size / 1024)
