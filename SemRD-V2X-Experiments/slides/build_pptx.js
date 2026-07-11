// SemRD-V2X 组会汇报 PPT 生成脚本
// 输出: project/SemRD-V2X-Experiments/slides/SemRD_V2X_Group_Meeting.pptx

const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";  // 13.333 x 7.5 inch
pres.title = "SemRD-V2X 组会汇报";
pres.company = "SJTU";
pres.author = "Xu Hu";

// ------- Palette (Ocean Gradient) -------
const C = {
  navy:    "0B1F3A",
  blue:    "065A82",
  teal:    "00A6D6",
  midnight:"1E2761",
  cream:   "F4F7FA",
  white:   "FFFFFF",
  gray:    "6E7A8A",
  charcoal:"2C3E50",
  accent:  "FFB000",   // core / highlight
  accent2: "F96167",   // gap / risk
  soft:    "CADCFC",   // supporting
  green:   "27AE60",   // done
};

// ------- Fonts -------
const F = {
  header: "Calibri",
  body:   "Calibri",
  mono:   "Consolas",
};

// ------- Helpers -------
function bg(slide, color) {
  slide.background = { color };
}

function titleBar(slide, title, subtitle, opts = {}) {
  const dark = opts.dark || false;
  const titleColor = dark ? C.white : C.navy;
  const subColor   = dark ? C.soft  : C.gray;
  slide.addText(title, {
    x: 0.5, y: 0.35, w: 12.3, h: 0.75,
    fontSize: 30, bold: true, color: titleColor,
    fontFace: F.header, align: "left", margin: 0,
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.5, y: 1.05, w: 12.3, h: 0.4,
      fontSize: 15, color: subColor,
      fontFace: F.body, align: "left", italic: true, margin: 0,
    });
  }
}

function pageBadge(slide, num, total) {
  slide.addText(`${num} / ${total}`, {
    x: 12.3, y: 7.05, w: 0.8, h: 0.3,
    fontSize: 10, color: C.gray, fontFace: F.body, align: "right",
  });
}

function projectFooter(slide) {
  slide.addText("SemRD-V2X · 演绎信源率失真 · V2X 协同感知", {
    x: 0.5, y: 7.05, w: 8, h: 0.3,
    fontSize: 10, color: C.gray, fontFace: F.body, italic: true,
  });
}

// Card with header strip + body
function card(slide, x, y, w, h, header, body, opts = {}) {
  const headerColor = opts.headerColor || C.blue;
  const bodyBg      = opts.bodyBg      || C.cream;
  const textColor   = opts.textColor   || C.charcoal;
  const headerText  = opts.headerText  || C.white;
  const headerH     = 0.4;

  slide.addShape(pres.ShapeType.rect, {
    x, y, w, h: headerH,
    fill: { color: headerColor }, line: { color: headerColor },
  });
  slide.addText(header, {
    x: x + 0.15, y, w: w - 0.3, h: headerH,
    fontSize: 13, bold: true, color: headerText, fontFace: F.header,
    valign: "middle", align: "left", margin: 0,
  });
  slide.addShape(pres.ShapeType.rect, {
    x, y: y + headerH, w, h: h - headerH,
    fill: { color: bodyBg }, line: { color: bodyBg },
  });
  if (Array.isArray(body)) {
    slide.addText(body.map(t => ({ text: t, options: { bullet: { code: "25CF" }, color: textColor } })), {
      x: x + 0.2, y: y + headerH + 0.05, w: w - 0.4, h: h - headerH - 0.1,
      fontSize: 12, fontFace: F.body, color: textColor, paraSpaceAfter: 3,
      valign: "top",
    });
  } else {
    slide.addText(body, {
      x: x + 0.2, y: y + headerH + 0.05, w: w - 0.4, h: h - headerH - 0.1,
      fontSize: 12, fontFace: F.body, color: textColor, valign: "top",
    });
  }
}

// ============================================================
// SLIDE 1 — 标题页
// ============================================================
{
  const s = pres.addSlide();
  bg(s, C.navy);

  // 左侧竖条
  s.addShape(pres.ShapeType.rect, {
    x: 0, y: 0, w: 0.25, h: 7.5, fill: { color: C.accent }, line: { color: C.accent },
  });

  s.addText("面向 V2X 协同感知的", {
    x: 0.8, y: 1.4, w: 12, h: 0.6,
    fontSize: 32, color: C.soft, fontFace: F.header, margin: 0,
  });
  s.addText("演绎信源率失真建模", {
    x: 0.8, y: 2.0, w: 12, h: 1.0,
    fontSize: 48, bold: true, color: C.white, fontFace: F.header, margin: 0,
  });
  s.addText("Deductive Source Coding for Communication-Efficient V2X Cooperative Perception", {
    x: 0.8, y: 3.05, w: 12, h: 0.5,
    fontSize: 18, color: C.teal, fontFace: F.body, italic: true, margin: 0,
  });

  // 副信息 (关键词)
  s.addText([
    { text: "V2X cooperative perception", options: { color: C.soft, bold: true } },
    { text: "   ·   ", options: { color: C.gray } },
    { text: "Rate-distortion theory", options: { color: C.soft, bold: true } },
    { text: "   ·   ", options: { color: C.gray } },
    { text: "Deductive source coding", options: { color: C.soft, bold: true } },
    { text: "   ·   ", options: { color: C.gray } },
    { text: "Closure fidelity", options: { color: C.soft, bold: true } },
  ], {
    x: 0.8, y: 3.75, w: 12, h: 0.4,
    fontSize: 13, fontFace: F.body, margin: 0,
  });

  // 底部块: 汇报人 + 日期 + 目标
  s.addShape(pres.ShapeType.rect, {
    x: 0.8, y: 5.4, w: 5.8, h: 1.6,
    fill: { color: C.midnight }, line: { color: C.accent, width: 0.5 },
  });
  s.addText([
    { text: "汇报人  ", options: { color: C.gray, fontSize: 11 } },
    { text: "Xu Hu\n", options: { color: C.white, fontSize: 16, bold: true } },
    { text: "所属  ", options: { color: C.gray, fontSize: 11 } },
    { text: "SJTU · Y2 PhD\n", options: { color: C.white, fontSize: 14 } },
    { text: "组会汇报  ", options: { color: C.gray, fontSize: 11 } },
    { text: "2026-07", options: { color: C.white, fontSize: 14 } },
  ], {
    x: 1.0, y: 5.55, w: 5.4, h: 1.3,
    fontFace: F.body, valign: "top", margin: 0,
  });

  s.addShape(pres.ShapeType.rect, {
    x: 6.9, y: 5.4, w: 5.8, h: 1.6,
    fill: { color: C.midnight }, line: { color: C.accent, width: 0.5 },
  });
  s.addText([
    { text: "研究目标\n", options: { color: C.accent, fontSize: 12, bold: true } },
    { text: "为 V2X 协同感知中的通信压缩\n", options: { color: C.white, fontSize: 14 } },
    { text: "提供 information-theoretic 下界\n", options: { color: C.white, fontSize: 14 } },
    { text: "并给出可训练的落地实现", options: { color: C.white, fontSize: 14 } },
  ], {
    x: 7.1, y: 5.55, w: 5.4, h: 1.3,
    fontFace: F.body, valign: "top", margin: 0,
  });

  // 右上小标: 面向 AAAI 预研
  s.addShape(pres.ShapeType.rect, {
    x: 10.6, y: 0.5, w: 2.2, h: 0.35,
    fill: { color: C.accent }, line: { color: C.accent },
  });
  s.addText("面向 AAAI 预研", {
    x: 10.6, y: 0.5, w: 2.2, h: 0.35,
    fontSize: 12, bold: true, color: C.navy, fontFace: F.header,
    align: "center", valign: "middle", margin: 0,
  });
}

// ============================================================
// SLIDE 2 — 背景: V2X 的必要性
// ============================================================
{
  const s = pres.addSlide();
  bg(s, C.white);
  titleBar(s, "背景：单车感知有物理盲区", "V2X 通过车-车-路协同扩大感知范围");

  // 左侧: 三大痛点
  card(s, 0.5, 1.7, 6.0, 5.0, "单车感知的三大痛点", [
    "遮挡问题：大车、建筑物、路口遮挡使 ego vehicle 看不到远处目标",
    "感知距离有限：单车 LiDAR 对远距离、小目标不稳定",
    "安全关键场景：路口/匝道/城市密集交通对提前感知要求高",
    "→ 单纯堆算力、堆传感器无法解决物理盲区",
  ], { headerColor: C.blue });

  // 右侧: V2X 方案图示
  card(s, 6.9, 1.7, 5.9, 5.0, "V2X 协同感知的思路", "", { headerColor: C.teal, bodyBg: C.cream });

  // 右侧内嵌简图: 3 个 agent + ego
  const gx = 7.2, gy = 2.5;
  // Ego
  s.addShape(pres.ShapeType.roundRect, {
    x: gx + 2.0, y: gy + 2.5, w: 1.5, h: 0.6,
    fill: { color: C.accent }, line: { color: C.accent }, rectRadius: 0.1,
  });
  s.addText("Ego Vehicle", {
    x: gx + 2.0, y: gy + 2.5, w: 1.5, h: 0.6,
    fontSize: 12, bold: true, color: C.navy, fontFace: F.header,
    align: "center", valign: "middle", margin: 0,
  });
  // Agents
  const agents = [
    { name: "Vehicle A",    x: gx + 0.1, y: gy + 0.2, col: C.blue },
    { name: "Vehicle B",    x: gx + 3.9, y: gy + 0.2, col: C.blue },
    { name: "Roadside RSU", x: gx + 2.0, y: gy + 0.2, col: C.midnight },
  ];
  agents.forEach(a => {
    s.addShape(pres.ShapeType.roundRect, {
      x: a.x, y: a.y, w: 1.5, h: 0.6,
      fill: { color: a.col }, line: { color: a.col }, rectRadius: 0.1,
    });
    s.addText(a.name, {
      x: a.x, y: a.y, w: 1.5, h: 0.6,
      fontSize: 12, bold: true, color: C.white, fontFace: F.header,
      align: "center", valign: "middle", margin: 0,
    });
    // 箭头到 ego
    s.addShape(pres.ShapeType.line, {
      x: a.x + 0.75, y: a.y + 0.6, w: (gx + 2.75) - (a.x + 0.75), h: (gy + 2.5) - (a.y + 0.6),
      line: { color: C.teal, width: 2, endArrowType: "triangle" },
    });
  });
  // "feature" 标签
  s.addText("shared feature maps", {
    x: gx + 0.5, y: gy + 1.4, w: 4.5, h: 0.3,
    fontSize: 11, italic: true, color: C.gray, fontFace: F.body,
    align: "center", margin: 0,
  });

  projectFooter(s);
  pageBadge(s, 2, 15);
}

// ============================================================
// SLIDE 3 — V2X pipeline
// ============================================================
{
  const s = pres.addSlide();
  bg(s, C.white);
  titleBar(s, "V2X 协同感知 pipeline", "多 agent 共享中间 BEV 特征，而不是原始点云");

  // 主 pipeline: 5 个 block
  const boxes = [
    { title: "LiDAR",        sub: "point cloud",       x: 0.5,  col: C.navy },
    { title: "PointPillar",  sub: "BEV feature F_i",   x: 3.0,  col: C.blue },
    { title: "Compression",  sub: "shared over V2X",   x: 5.5,  col: C.teal },
    { title: "Fusion (HMSA)",sub: "multi-agent attn",  x: 8.0,  col: C.midnight },
    { title: "Detection",    sub: "3D bbox",           x: 10.5, col: C.accent },
  ];
  const by = 2.0, bw = 2.3, bh = 1.3;
  boxes.forEach((b, i) => {
    const isAcc = b.col === C.accent;
    s.addShape(pres.ShapeType.roundRect, {
      x: b.x, y: by, w: bw, h: bh,
      fill: { color: b.col }, line: { color: b.col }, rectRadius: 0.08,
    });
    s.addText(b.title, {
      x: b.x, y: by + 0.15, w: bw, h: 0.5,
      fontSize: 15, bold: true, color: isAcc ? C.navy : C.white, fontFace: F.header,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText(b.sub, {
      x: b.x, y: by + 0.7, w: bw, h: 0.5,
      fontSize: 11, color: isAcc ? C.navy : C.soft, fontFace: F.body,
      align: "center", valign: "middle", italic: true, margin: 0,
    });
    // 箭头
    if (i < boxes.length - 1) {
      s.addShape(pres.ShapeType.line, {
        x: b.x + bw, y: by + bh / 2, w: 0.2, h: 0, line: { color: C.gray, width: 2, endArrowType: "triangle" },
      });
    }
  });

  // 关键要点
  s.addText([
    { text: "关键：", options: { bold: true, color: C.accent2 } },
    { text: "通信的不是最终 detection，也不是 raw LiDAR，而是 ", options: { color: C.charcoal } },
    { text: "中间 BEV feature map", options: { bold: true, color: C.blue } },
    { text: " —— 这正是带宽瓶颈的来源。", options: { color: C.charcoal } },
  ], {
    x: 0.5, y: 3.9, w: 12.3, h: 0.5,
    fontSize: 15, fontFace: F.body, margin: 0,
  });

  // 下方两个说明卡
  card(s, 0.5, 4.7, 6.0, 2.2, "以 V2X-ViTv2 为例", [
    "PointPillar 提取 per-agent BEV feature (256×48×176)",
    "1×1 conv 通道压缩后广播给 ego vehicle",
    "HMSA：区分车/路两类 agent 的异构注意力",
    "MSPA：多尺度池化注意力捕捉不同视野范围",
  ], { headerColor: C.blue });

  card(s, 6.9, 4.7, 5.9, 2.2, "本项目关注的环节", [
    "研究红色 Compression 环节：什么信息必须传？",
    "在 Fusion 前引入 Core Selection 和 Inference",
    "不改动 detection head，保持公平对比",
  ], { headerColor: C.accent2 });

  projectFooter(s);
  pageBadge(s, 3, 15);
}

// ============================================================
// SLIDE 4 — 通信带宽瓶颈
// ============================================================
{
  const s = pres.addSlide();
  bg(s, C.white);
  titleBar(s, "核心瓶颈：通信带宽 vs 感知性能", "协同越强，通信压力越大");

  // 左侧: 数字对比
  card(s, 0.5, 1.7, 6.0, 5.0, "V2XSet 上的典型数字", "", { headerColor: C.navy });

  const stats = [
    { name: "No Fusion (单车)",  ap: "0.402", bw: "0 MB",    col: C.gray },
    { name: "Late Fusion",       ap: "0.307", bw: "0.8 MB",  col: C.gray },
    { name: "Early Fusion",      ap: "0.384", bw: "48 MB",   col: C.accent2 },
    { name: "V2X-ViTv2 (SOTA)",  ap: "0.672", bw: "1.5 MB",  col: C.blue },
  ];
  stats.forEach((st, i) => {
    const y = 2.3 + i * 0.95;
    s.addShape(pres.ShapeType.rect, {
      x: 0.7, y, w: 0.15, h: 0.75, fill: { color: st.col }, line: { color: st.col },
    });
    s.addText(st.name, {
      x: 1.0, y, w: 3.0, h: 0.35,
      fontSize: 13, bold: true, color: C.charcoal, fontFace: F.body, valign: "middle", margin: 0,
    });
    s.addText([
      { text: "AP@0.7 ", options: { color: C.gray, fontSize: 10 } },
      { text: st.ap, options: { color: C.charcoal, fontSize: 13, bold: true } },
      { text: "     BW ", options: { color: C.gray, fontSize: 10 } },
      { text: st.bw, options: { color: C.charcoal, fontSize: 13, bold: true } },
    ], {
      x: 1.0, y: y + 0.35, w: 5.0, h: 0.35,
      fontFace: F.mono, valign: "middle", margin: 0,
    });
  });

  s.addText("数据来源: V2X-ViTv2 TPAMI 2025 · V2XSet Noisy Setting", {
    x: 0.7, y: 6.3, w: 5.7, h: 0.3,
    fontSize: 10, italic: true, color: C.gray, fontFace: F.body, margin: 0,
  });

  // 右侧: 瓶颈来源
  card(s, 6.9, 1.7, 5.9, 5.0, "为什么中间特征共享贵？", [
    "每个 agent 都要发送 dense BEV feature map",
    "带宽随 N × H × W × C 线性增长（N=5, H×W=8448, C=256）",
    "单帧未压缩理论上高达 34 MB / agent",
    "真实部署面临：\n  · 高带宽占用\n  · 传输延迟 → 位姿失配\n  · 弱信道下丢包放大误差",
  ], { headerColor: C.accent2 });

  // 中间大问题
  s.addShape(pres.ShapeType.rect, {
    x: 6.9, y: 6.8, w: 5.9, h: 0, line: { color: C.accent, width: 2 },
  });

  projectFooter(s);
  pageBadge(s, 4, 15);
}

// ============================================================
// SLIDE 5 — 现有方法及其局限
// ============================================================
{
  const s = pres.addSlide();
  bg(s, C.white);
  titleBar(s, "现有方法：会压缩，但缺理论下界", "都在回答 “how to compress”，很少回答 “how much is necessary”");

  // 表格
  const rows = [
    { m: "Where2Comm",   idea: "Spatial confidence map 决定哪里通信",     lim: "启发式选择，无理论最小率" },
    { m: "How2Comm",     idea: "选择协作者 + 内容",                        lim: "偏工程化，理论解释弱" },
    { m: "DiscoNet",     idea: "蒸馏协作图 (teacher-student)",             lim: "依赖 teacher 与图设计" },
    { m: "V2X-ViT / v2", idea: "Transformer 融合多 agent feature",         lim: "提升性能，但不回答最少传多少" },
  ];

  // Header
  const cols = [ { x: 0.5, w: 2.6 }, { x: 3.2, w: 5.0 }, { x: 8.3, w: 4.5 } ];
  const titles = ["方法", "核心思想", "局限"];
  s.addShape(pres.ShapeType.rect, {
    x: 0.5, y: 1.7, w: 12.3, h: 0.5,
    fill: { color: C.navy }, line: { color: C.navy },
  });
  titles.forEach((t, i) => {
    s.addText(t, {
      x: cols[i].x, y: 1.7, w: cols[i].w, h: 0.5,
      fontSize: 14, bold: true, color: C.white, fontFace: F.header,
      valign: "middle", align: "left", margin: 0,
    });
  });
  // Rows
  rows.forEach((r, i) => {
    const y = 2.2 + i * 0.7;
    const bg = i % 2 === 0 ? C.cream : C.white;
    s.addShape(pres.ShapeType.rect, {
      x: 0.5, y, w: 12.3, h: 0.7,
      fill: { color: bg }, line: { color: bg },
    });
    s.addText(r.m, {
      x: cols[0].x, y, w: cols[0].w, h: 0.7,
      fontSize: 13, bold: true, color: C.blue, fontFace: F.header, valign: "middle", margin: 0,
    });
    s.addText(r.idea, {
      x: cols[1].x, y, w: cols[1].w, h: 0.7,
      fontSize: 12, color: C.charcoal, fontFace: F.body, valign: "middle", margin: 0,
    });
    s.addText(r.lim, {
      x: cols[2].x, y, w: cols[2].w, h: 0.7,
      fontSize: 12, color: C.accent2, fontFace: F.body, italic: true, valign: "middle", margin: 0,
    });
  });

  // Gap 结论
  const gy = 5.4;
  s.addShape(pres.ShapeType.rect, {
    x: 0.5, y: gy, w: 12.3, h: 1.5,
    fill: { color: C.midnight }, line: { color: C.midnight },
  });
  s.addText([
    { text: "研究 gap\n", options: { fontSize: 15, bold: true, color: C.accent } },
    { text: "现有方法回答：", options: { fontSize: 14, color: C.soft } },
    { text: "How to compress?  ", options: { fontSize: 15, bold: true, color: C.white, fontFace: F.mono } },
    { text: "但很少回答：", options: { fontSize: 14, color: C.soft } },
    { text: "What is the minimum communication rate that preserves perceptual understanding?",
      options: { fontSize: 15, bold: true, color: C.accent, fontFace: F.mono } },
  ], {
    x: 0.8, y: gy + 0.15, w: 11.7, h: 1.2,
    fontFace: F.body, valign: "top", margin: 0,
  });

  projectFooter(s);
  pageBadge(s, 5, 15);
}

// ============================================================
// SLIDE 6 — 核心研究问题
// ============================================================
{
  const s = pres.addSlide();
  bg(s, C.white);
  titleBar(s, "核心研究问题", "V2X 感知中“必须传的信息”是什么？");

  // 三个大问题卡
  const qs = [
    { n: "Q1", t: "信息论问题", body: "在保持感知语义不变的条件下，最低通信率是多少？\n是否存在一个可计算的 lower bound？",
      col: C.blue },
    { n: "Q2", t: "结构问题",   body: "哪些特征无法由其他特征推导出来（core）？\n哪些是可以在接收端重建的冗余？",
      col: C.teal },
    { n: "Q3", t: "系统问题",   body: "能否设计一个可训练的模块，近似选择 core 并\n在接收端重建 redundant features？",
      col: C.midnight },
  ];
  qs.forEach((q, i) => {
    const x = 0.5 + i * 4.27;
    // 编号大圆
    s.addShape(pres.ShapeType.ellipse, {
      x: x + 0.2, y: 1.75, w: 0.8, h: 0.8,
      fill: { color: q.col }, line: { color: q.col },
    });
    s.addText(q.n, {
      x: x + 0.2, y: 1.75, w: 0.8, h: 0.8,
      fontSize: 20, bold: true, color: C.white, fontFace: F.header,
      align: "center", valign: "middle", margin: 0,
    });
    // 标题
    s.addText(q.t, {
      x: x + 1.15, y: 1.9, w: 2.8, h: 0.6,
      fontSize: 20, bold: true, color: q.col, fontFace: F.header, margin: 0,
    });
    // body 卡
    s.addShape(pres.ShapeType.rect, {
      x, y: 2.7, w: 4.1, h: 2.4,
      fill: { color: C.cream }, line: { color: q.col, width: 1 },
    });
    s.addText(q.body, {
      x: x + 0.2, y: 2.85, w: 3.7, h: 2.1,
      fontSize: 14, color: C.charcoal, fontFace: F.body, valign: "top", margin: 0,
    });
  });

  // 底部漏斗
  s.addText("研究思路的三级漏斗", {
    x: 0.5, y: 5.4, w: 12.3, h: 0.4,
    fontSize: 14, bold: true, color: C.navy, fontFace: F.header, align: "center", margin: 0,
  });

  const funnel = [
    { t: "Dense feature map  S", w: 8.0,  col: C.gray },
    { t: "Remove redundant   →  S \\ J", w: 6.0, col: C.blue },
    { t: "Transmit core      A ⊂ S", w: 4.0, col: C.accent },
  ];
  funnel.forEach((f, i) => {
    const w = f.w;
    const x = (13.333 - w) / 2;
    const y = 5.9 + i * 0.4;
    s.addShape(pres.ShapeType.rect, {
      x, y, w, h: 0.32,
      fill: { color: f.col }, line: { color: f.col },
    });
    const isAcc = f.col === C.accent;
    s.addText(f.t, {
      x, y, w, h: 0.32,
      fontSize: 12, bold: true, color: isAcc ? C.navy : C.white,
      fontFace: F.mono, align: "center", valign: "middle", margin: 0,
    });
  });

  projectFooter(s);
  pageBadge(s, 6, 15);
}

// ============================================================
// SLIDE 7 — 理论工具: 演绎信源 & closure fidelity
// ============================================================
{
  const s = pres.addSlide();
  bg(s, C.white);
  titleBar(s, "理论工具：Deductive Source Coding", "闭包保持保真度 (Closure-Preserving Fidelity)");

  // 左侧: 四个核心对象
  card(s, 0.5, 1.7, 6.0, 5.0, "四个核心对象", [
    "知识库 S — 一组 statements/facts",
    "证明系统 PS — 从子集推出新 statement 的规则集",
    "闭包 Cn(S) = { s : S ⊢ s }  — 所有能被推出的语义后果",
    "Closure fidelity — 不要求重建原始 S，而要求：Cn(Ŝ) = Cn(S)",
  ], { headerColor: C.blue });

  // 右侧: 传统 vs 演绎
  card(s, 6.9, 1.7, 5.9, 2.4, "传统信源压缩", [
    "目标：重建每一个原始符号",
    "失真 = 符号级差异（Hamming、L2、…）",
    "所有冗余都被视作“需要传的信息”",
  ], { headerColor: C.gray });

  card(s, 6.9, 4.3, 5.9, 2.4, "演绎信源压缩（本项目采用）", [
    "目标：重建符号所能推出的一切",
    "失真 = closure 的差异（Jaccard 类）",
    "冗余在信息论意义下不可见，天然被“免费”重建",
  ], { headerColor: C.accent, headerText: C.navy });

  // 底部关键式
  s.addShape(pres.ShapeType.rect, {
    x: 0.5, y: 6.85, w: 12.3, h: 0.3,
    fill: { color: C.navy }, line: { color: C.navy },
  });
  s.addText([
    { text: "关键条件：",     options: { color: C.accent, bold: true } },
    { text: "Cn(Ŝ) = Cn(S) ", options: { color: C.white, bold: true, fontFace: F.mono } },
    { text: "  ⇒  重建保持所有语义后果（推理不变）", options: { color: C.soft } },
  ], {
    x: 0.5, y: 6.85, w: 12.3, h: 0.3,
    fontSize: 13, fontFace: F.body, valign: "middle", align: "center", margin: 0,
  });

  pageBadge(s, 7, 15);
}

// ============================================================
// SLIDE 8 — irredundant core 直觉
// ============================================================
{
  const s = pres.addSlide();
  bg(s, C.white);
  titleBar(s, "关键概念：Irredundant Core", "真正需要传的，是不可推导的 “原子事实”");

  // 左侧: 分解式
  card(s, 0.5, 1.7, 6.0, 5.0, "S 的规范分解", [
    "S = A  ⊍  J",
    "  A  =  irredundant core / atoms（不可从其他推出）",
    "  J  =  redundant part（可由 A 推出）",
    "核心性质：Cn(A) = Cn(S)",
    "⇒  只要发送 A，接收端仍能恢复整个 closure",
    "⇒  发送 J 不会额外增加语义信息，但会占带宽",
  ], { headerColor: C.blue });

  // 右侧: 定理框
  card(s, 6.9, 1.7, 5.9, 2.6, "关键理论结果 (Xu 2026, Thm 3.14)", "", { headerColor: C.accent, headerText: C.navy });

  s.addText([
    { text: "零失真率\n", options: { color: C.blue, fontSize: 12, bold: true } },
    { text: "R(0) = P_A · H(π_A)\n\n", options: { color: C.navy, fontSize: 22, bold: true, fontFace: F.mono } },
    { text: "P_A：source 落在 core 上的概率质量\n", options: { color: C.charcoal, fontSize: 12 } },
    { text: "H(π_A)：core 内部分布的熵\n", options: { color: C.charcoal, fontSize: 12 } },
    { text: "redundant part 对 rate 与 distortion 都不可见", options: { color: C.accent2, fontSize: 12, italic: true } },
  ], {
    x: 7.1, y: 2.25, w: 5.5, h: 2.0,
    fontFace: F.body, valign: "top", margin: 0,
  });

  // 右下: 一个玩具示例
  card(s, 6.9, 4.5, 5.9, 2.2, "一个玩具直觉", [
    "假设有 12 个 statement，其中只有 4 个是 core",
    "P_A = 4/12 = 1/3",
    "若 core 分布均匀：H(π_A) = log 4 = 2 bits",
    "R(0) = 1/3 × 2 ≈ 0.67 bit/symbol",
    "远低于把全部 12 个都当独立信源的 log 12 ≈ 3.58 bit",
  ], { headerColor: C.teal });

  projectFooter(s);
  pageBadge(s, 8, 15);
}

// ============================================================
// SLIDE 9 — V2X → deductive source 映射
// ============================================================
{
  const s = pres.addSlide();
  bg(s, C.white);
  titleBar(s, "V2X → 演绎信源的映射", "把 BEV feature 中的空间位置视为 perceptual statement");

  // 左侧: 映射表
  const map = [
    { l: "statement s",       r: "某 agent 在 BEV (h,w) 的 feature vector" },
    { l: "knowledge base S",  r: "所有 agent 的 feature maps 汇总" },
    { l: "proof system PS",   r: "空间/多视角/语义推理规则 R1-R4" },
    { l: "closure Cn(S)",     r: "可推导出的完整场景理解" },
    { l: "irredundant core A",r: "不可由其他特征推导的关键位置" },
    { l: "redundant part J",  r: "可由邻域/多视角/语义补全的特征" },
    { l: "inference depth δ", r: "decoder 端传播 / 重建层数" },
  ];
  // Header
  s.addShape(pres.ShapeType.rect, {
    x: 0.5, y: 1.7, w: 7.2, h: 0.4, fill: { color: C.navy }, line: { color: C.navy },
  });
  s.addText("演绎信源概念", {
    x: 0.6, y: 1.7, w: 2.4, h: 0.4,
    fontSize: 12, bold: true, color: C.white, fontFace: F.header, valign: "middle", margin: 0,
  });
  s.addText("V2X 对应物", {
    x: 3.1, y: 1.7, w: 4.5, h: 0.4,
    fontSize: 12, bold: true, color: C.white, fontFace: F.header, valign: "middle", margin: 0,
  });
  map.forEach((row, i) => {
    const y = 2.1 + i * 0.5;
    const bg = i % 2 === 0 ? C.cream : C.white;
    s.addShape(pres.ShapeType.rect, {
      x: 0.5, y, w: 7.2, h: 0.5,
      fill: { color: bg }, line: { color: bg },
    });
    s.addText(row.l, {
      x: 0.6, y, w: 2.4, h: 0.5,
      fontSize: 11, bold: true, color: C.blue, fontFace: F.mono, valign: "middle", margin: 0,
    });
    s.addText(row.r, {
      x: 3.1, y, w: 4.5, h: 0.5,
      fontSize: 11, color: C.charcoal, fontFace: F.body, valign: "middle", margin: 0,
    });
  });

  // 右侧: 四类推理规则
  card(s, 7.9, 1.7, 4.9, 4.9, "四类感知推理规则", "", { headerColor: C.teal });
  const rules = [
    { n: "R1", t: "Neighborhood Propagation", d: "邻域位置可推出弱化版本" },
    { n: "R2", t: "Multi-View Confirmation",  d: "多 agent 一致观测互相确认" },
    { n: "R3", t: "Semantic Completion",      d: "部分观测可推出完整语义" },
    { n: "R4", t: "Infra → Vehicle Transfer", d: "路侧视角推出车端特征" },
  ];
  rules.forEach((r, i) => {
    const y = 2.25 + i * 0.95;
    // 编号色块
    s.addShape(pres.ShapeType.rect, {
      x: 8.1, y, w: 0.6, h: 0.7,
      fill: { color: C.teal }, line: { color: C.teal },
    });
    s.addText(r.n, {
      x: 8.1, y, w: 0.6, h: 0.7,
      fontSize: 15, bold: true, color: C.white, fontFace: F.header,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText([
      { text: r.t + "\n", options: { bold: true, color: C.navy, fontSize: 13 } },
      { text: r.d, options: { color: C.charcoal, fontSize: 11 } },
    ], {
      x: 8.85, y, w: 3.9, h: 0.7,
      fontFace: F.body, valign: "middle", margin: 0,
    });
  });

  // 备注
  s.addText([
    { text: "当前实现：", options: { bold: true, color: C.accent2 } },
    { text: "主要落地 R1 的连续松弛（δ-layer 卷积传播），R2-R4 作为后续扩展", options: { color: C.charcoal } },
  ], {
    x: 0.5, y: 6.75, w: 12.3, h: 0.35,
    fontSize: 12, fontFace: F.body, italic: true, margin: 0,
  });

  pageBadge(s, 9, 15);
}

// ============================================================
// SLIDE 10 — 方法概览
// ============================================================
{
  const s = pres.addSlide();
  bg(s, C.white);
  titleBar(s, "系统设计：先选 core，再由 decoder 推理重建", "在 V2X-ViT 基础上加三个模块，backbone 保持不变");

  // 顶部 pipeline
  const pipeY = 1.75;
  const bh2 = 0.9;
  const nodes = [
    { t: "Agent BEV",         sub: "F_i (256×48×176)", x: 0.5,  w: 1.9, col: C.navy, new: false },
    { t: "Core Selection",    sub: "CSM · learn A_i",   x: 2.55, w: 1.9, col: C.accent, new: true },
    { t: "Transmit core",     sub: "sparse 通信",        x: 4.6,  w: 1.9, col: C.blue,   new: false },
    { t: "Inference Module",  sub: "IM · δ-layer 推理",  x: 6.65, w: 1.9, col: C.accent, new: true },
    { t: "V2X-ViT Fusion",    sub: "HMSA",              x: 8.7,  w: 1.9, col: C.blue,   new: false },
    { t: "Detection",         sub: "3D bbox",           x: 10.75,w: 1.9, col: C.midnight, new: false },
  ];
  nodes.forEach((n, i) => {
    const isAcc = n.col === C.accent;
    s.addShape(pres.ShapeType.roundRect, {
      x: n.x, y: pipeY, w: n.w, h: bh2,
      fill: { color: n.col }, line: { color: n.new ? C.accent2 : n.col, width: n.new ? 2.5 : 0 },
      rectRadius: 0.08,
    });
    s.addText(n.t, {
      x: n.x, y: pipeY + 0.05, w: n.w, h: 0.4,
      fontSize: 12, bold: true, color: isAcc ? C.navy : C.white, fontFace: F.header,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText(n.sub, {
      x: n.x, y: pipeY + 0.45, w: n.w, h: 0.4,
      fontSize: 10, color: isAcc ? C.navy : C.soft, fontFace: F.body,
      align: "center", valign: "middle", italic: true, margin: 0,
    });
    // 新模块标签
    if (n.new) {
      s.addShape(pres.ShapeType.rect, {
        x: n.x, y: pipeY - 0.28, w: n.w, h: 0.22,
        fill: { color: C.accent2 }, line: { color: C.accent2 },
      });
      s.addText("NEW", {
        x: n.x, y: pipeY - 0.28, w: n.w, h: 0.22,
        fontSize: 10, bold: true, color: C.white, fontFace: F.header,
        align: "center", valign: "middle", margin: 0,
      });
    }
    if (i < nodes.length - 1) {
      s.addShape(pres.ShapeType.line, {
        x: n.x + n.w, y: pipeY + bh2 / 2, w: 0.15, h: 0,
        line: { color: C.gray, width: 2, endArrowType: "triangle" },
      });
    }
  });

  // 三个新模块解释卡
  const modules = [
    { t: "Core Selection Module (CSM)",
      body: [
        "MLP 打分：为每个 (h,w) 计算 importance",
        "Gumbel-Softmax + top-k：可微 core 选择",
        "输出 mask，冗余位置置 0",
      ],
      col: C.blue },
    { t: "Differentiable Inference Module (IM)",
      body: [
        "δ 层卷积 + 邻域传播（对应 R1）",
        "core 位置保持不变，redundant 位置被重建",
        "以计算换通信：δ↑ → 需传的越少",
      ],
      col: C.teal },
    { t: "Rate Regularization (RR)",
      body: [
        "L_rate = λ · P_A · H(π_A)  近似理论下界",
        "训练时鼓励 mask 稀疏 + core 分布集中",
        "推理时可通过 P_A 手动调节",
      ],
      col: C.midnight },
  ];
  modules.forEach((m, i) => {
    const x = 0.5 + i * 4.27;
    const y = 3.5;
    card(s, x, y, 4.1, 3.4, m.t, m.body, { headerColor: m.col });
  });

  projectFooter(s);
  pageBadge(s, 10, 15);
}

// ============================================================
// SLIDE 11 — 理论预期
// ============================================================
{
  const s = pres.addSlide();
  bg(s, C.white);
  titleBar(s, "理论预期：通信率由 core 决定", "用计算换通信 —— 更深的 decoder 推理可以传更少的 core");

  // 三个关键定理
  card(s, 0.5, 1.7, 4.1, 5.0, "零失真率", "", { headerColor: C.blue });
  s.addText([
    { text: "R(0) = P_A · H(π_A)\n\n", options: { fontSize: 22, bold: true, color: C.navy, fontFace: F.mono } },
    { text: "在 disjoint core 假设下，", options: { fontSize: 12, color: C.charcoal } },
    { text: "V2X 感知无失真通信率\n", options: { fontSize: 12, color: C.charcoal } },
    { text: "= 核心 mass × 核心分布的熵\n\n", options: { fontSize: 12, color: C.charcoal } },
    { text: "→ 冗余部分不占率\n", options: { fontSize: 12, color: C.accent2, italic: true } },
    { text: "→ 传统 Hamming 视角严格劣于闭包视角", options: { fontSize: 12, color: C.accent2, italic: true } },
  ], {
    x: 0.7, y: 2.25, w: 3.7, h: 4.4,
    fontFace: F.body, valign: "top", margin: 0,
  });

  card(s, 4.8, 1.7, 4.1, 5.0, "全率失真曲线", "", { headerColor: C.teal });
  s.addText([
    { text: "R(D) = P_A · R^{(A)}(D/P_A)\n\n", options: { fontSize: 18, bold: true, color: C.navy, fontFace: F.mono } },
    { text: "全局 rate-distortion 曲线由\n", options: { fontSize: 12, color: C.charcoal } },
    { text: "只在 core 上定义的子问题决定\n\n", options: { fontSize: 12, color: C.charcoal } },
    { text: "→ redundant part 对 rate 和\n     distortion 都完全不可见\n\n", options: { fontSize: 12, color: C.accent2, italic: true } },
    { text: "→ 允许对 core 独立设计压缩策略", options: { fontSize: 12, color: C.accent2, italic: true } },
  ], {
    x: 5.0, y: 2.25, w: 3.7, h: 4.4,
    fontFace: F.body, valign: "top", margin: 0,
  });

  card(s, 9.1, 1.7, 3.7, 5.0, "推理深度权衡", "", { headerColor: C.midnight });
  s.addText([
    { text: "R(D, δ) = P_δ · R^{(A_δ)}(D/P_δ)\n\n", options: { fontSize: 16, bold: true, color: C.navy, fontFace: F.mono } },
    { text: "δ = 0 → 退化为 Hamming\n", options: { fontSize: 12, color: C.charcoal } },
    { text: "δ ↑ → 更多 redundant 可推\n", options: { fontSize: 12, color: C.charcoal } },
    { text: "δ ≥ D_d → 完全闭包压缩\n\n", options: { fontSize: 12, color: C.charcoal } },
    { text: "→ 可以用 decoder 端算力\n     直接换来通信节省", options: { fontSize: 12, color: C.accent, bold: true } },
  ], {
    x: 9.3, y: 2.25, w: 3.3, h: 4.4,
    fontFace: F.body, valign: "top", margin: 0,
  });

  // 底部核心 tradeoff
  s.addShape(pres.ShapeType.rect, {
    x: 0.5, y: 6.85, w: 12.3, h: 0.3,
    fill: { color: C.accent }, line: { color: C.accent },
  });
  s.addText("三轴权衡  ·  Bandwidth  ↔  Accuracy  ↔  Decoder Computation", {
    x: 0.5, y: 6.85, w: 12.3, h: 0.3,
    fontSize: 13, bold: true, color: C.navy, fontFace: F.mono, align: "center", valign: "middle", margin: 0,
  });

  pageBadge(s, 11, 15);
}

// ============================================================
// SLIDE 12 — 实验设计
// ============================================================
{
  const s = pres.addSlide();
  bg(s, C.white);
  titleBar(s, "实验设计：验证 “少传 core + decoder 推理” 的有效性", "在 V2XSet 上从核心压缩曲线、深度分析、理论下界三个维度评估");

  // 上半: 实验矩阵表
  s.addText("POC 实验矩阵（V2XSet, Noisy Setting）", {
    x: 0.5, y: 1.65, w: 12.3, h: 0.35,
    fontSize: 14, bold: true, color: C.navy, fontFace: F.header, margin: 0,
  });
  const cols = [
    { t: "Run",       x: 0.5,  w: 0.9 },
    { t: "P_A",       x: 1.4,  w: 1.0 },
    { t: "δ",         x: 2.4,  w: 0.9 },
    { t: "Rate Reg",  x: 3.3,  w: 1.3 },
    { t: "回答的问题", x: 4.6,  w: 8.2 },
  ];
  const runs = [
    { r: "R1", pa: "1.0", d: "0", rr: "off", q: "Baseline（等价 V2X-ViT v1，pipeline sanity check）" },
    { r: "R2", pa: "0.5", d: "0", rr: "off", q: "CSM only，无 IM：单纯少传，AP 掉多少？" },
    { r: "R3", pa: "0.5", d: "3", rr: "off", q: "CSM + IM：decoder 推理能否补回性能？" },
    { r: "R4", pa: "0.2", d: "3", rr: "off", q: "激进压缩下（80% ↓ BW）性能损失几何？" },
    { r: "R5", pa: "0.2", d: "3", rr: "on",  q: "率正则化是否进一步逼近理论下界？" },
  ];
  const rowY0 = 2.05;
  const rowH = 0.42;
  // header
  s.addShape(pres.ShapeType.rect, {
    x: 0.5, y: rowY0, w: 12.3, h: 0.4, fill: { color: C.navy }, line: { color: C.navy },
  });
  cols.forEach(c => {
    s.addText(c.t, {
      x: c.x, y: rowY0, w: c.w, h: 0.4,
      fontSize: 11, bold: true, color: C.white, fontFace: F.header, valign: "middle", margin: 0,
    });
  });
  runs.forEach((r, i) => {
    const y = rowY0 + 0.4 + i * rowH;
    const bg = i % 2 === 0 ? C.cream : C.white;
    s.addShape(pres.ShapeType.rect, {
      x: 0.5, y, w: 12.3, h: rowH,
      fill: { color: bg }, line: { color: bg },
    });
    const cells = [r.r, r.pa, r.d, r.rr, r.q];
    cells.forEach((v, j) => {
      const isFirst = j === 0;
      s.addText(v, {
        x: cols[j].x, y, w: cols[j].w, h: rowH,
        fontSize: 11, bold: isFirst, fontFace: j === 4 ? F.body : F.mono,
        color: isFirst ? C.blue : C.charcoal,
        valign: "middle", margin: 0,
      });
    });
  });

  // 下半: 三个卡
  const infoY = 4.7;
  card(s, 0.5, infoY, 4.1, 2.3, "数据集", [
    "V2XSet (CARLA, 11,447 帧)",
    "Perfect + Noisy 两种设置",
    "后续可扩展 DAIR-V2X（真实场景）",
  ], { headerColor: C.blue });

  card(s, 4.8, infoY, 4.1, 2.3, "评估指标", [
    "AP@0.5 / AP@0.7 — 检测性能",
    "Bandwidth (MB/frame) — 实测通信开销",
    "Core mass P_A — 学习到的稀疏比例",
    "Latency (ms) — 加 IM 后的延迟",
    "|R_empirical − P_A · H(π_A)| — 与理论下界差距",
  ], { headerColor: C.teal });

  card(s, 9.1, infoY, 3.7, 2.3, "扩展实验（若时间充足）", [
    "Depth sweep：δ ∈ {0,1,2,3,4}",
    "Robustness：xyz/heading 噪声",
    "Heterogeneous：DAIR-V2X 车-路异构",
    "Ablation：learned vs random core，w/ vs w/o IM/RR",
  ], { headerColor: C.midnight });

  pageBadge(s, 12, 15);
}

// ============================================================
// SLIDE 13 — 当前进展
// ============================================================
{
  const s = pres.addSlide();
  bg(s, C.white);
  titleBar(s, "当前进展", "理论骨架和代码框架已经跑通，真实数字待补");

  // 三列: Done / In Progress / To-Do
  const cols3 = [
    { t: "✔  已完成", col: C.green, items: [
      "深度阅读导师 Rate-Distortion for Deductive Sources",
      "完成 V2X → 演绎信源的概念映射（Table 4.1）",
      "完成论文初稿骨架（Section 3-6）",
      "基于 V2X-ViT v1 搭建实验代码 [SemRD-V2X-Experiments](project/SemRD-V2X-Experiments/)",
      "实现三个新模块：CSM / IM / RR",
      "训练 / 评估 / 带宽测量脚本",
      "单元测试 5/5 通过（模块 forward + 数值正确性）",
    ]},
    { t: "▶  正在进行", col: C.accent, items: [
      "V2XSet 数据解压与预处理（train ~52GB，validate/test 完成）",
      "训练 pipeline 联调（已解决 Cython 编译、opencv Qt5、spconv/cumm、shm 等问题）",
      "Baseline (P_A=1.0, δ=0) 在 3× A800 上启动",
    ]},
    { t: "▷  待推进", col: C.accent2, items: [
      "跑完 R1–R5 五个核心实验",
      "计算 H(π_A) 用于理论 vs 实测对比",
      "画 rate-distortion 曲线（Figure 1）",
      "填补 Section 7 全部 6 张表",
      "重写 abstract 和 Section 1 引言",
    ]},
  ];
  cols3.forEach((col, i) => {
    const x = 0.5 + i * 4.27;
    card(s, x, 1.7, 4.1, 5.3, col.t, col.items, { headerColor: col.col, headerText: (col.col === C.accent ? C.navy : C.white) });
  });

  // 底部诚实说明
  s.addShape(pres.ShapeType.rect, {
    x: 0.5, y: 7.05, w: 12.3, h: 0.3,
    fill: { color: C.midnight }, line: { color: C.midnight },
  });
  s.addText([
    { text: "⚠  ", options: { color: C.accent, bold: true, fontSize: 12 } },
    { text: "重要说明：", options: { color: C.accent, bold: true, fontSize: 12 } },
    { text: "论文当前 Section 7 表格中的 Ours 数字均为占位符（TODO），不能作为最终结论", options: { color: C.white, fontSize: 12 } },
  ], {
    x: 0.5, y: 7.05, w: 12.3, h: 0.3,
    fontFace: F.body, valign: "middle", align: "center", margin: 0,
  });

  pageBadge(s, 13, 15);
}

// ============================================================
// SLIDE 14 — 风险与待解决问题
// ============================================================
{
  const s = pres.addSlide();
  bg(s, C.white);
  titleBar(s, "风险与待解决问题", "诚实列出目前尚未完全解决的四个问题");

  const risks = [
    { n: "R1", t: "理论 vs 连续特征的 gap",
      cause: "导师理论建立在离散 Horn/Datalog closure 上，而 V2X feature 是连续向量",
      plan:  "将实现定位为 continuous relaxation；在 Section 8 明确讨论 Tarski 公理在连续空间的近似性",
      col: C.accent2 },
    { n: "R2", t: "R2–R4 尚未完全实现",
      cause: "当前 IM 主要落地 R1 邻域传播，多视角/语义/异构规则暂缺",
      plan:  "先用 R1 验证是否已能带来收益；有余力再补 cross-agent attention 实现 R2/R4",
      col: C.accent },
    { n: "R3", t: "使用 V2X-ViT v1 而非 v2",
      cause: "V2X-ViTv2 官方代码未公开",
      plan:  "明确说明方法与 backbone 正交；结论对 v2 仍然成立；未来如复现 v2 再迁移",
      col: C.blue },
    { n: "R4", t: "真实实验成本高",
      cause: "V2XSet 单个 run ~20h @ A800，POC 5 run ≈ 4-5 天",
      plan:  "先完成 R1–R3 三个最关键的 run；其他实验并行 A800 三卡跑，或缩至 30 epoch",
      col: C.teal },
  ];
  risks.forEach((r, i) => {
    const y = 1.7 + i * 1.35;
    // 编号
    s.addShape(pres.ShapeType.rect, {
      x: 0.5, y, w: 0.9, h: 1.2,
      fill: { color: r.col }, line: { color: r.col },
    });
    s.addText(r.n, {
      x: 0.5, y, w: 0.9, h: 1.2,
      fontSize: 24, bold: true, color: C.white, fontFace: F.header,
      align: "center", valign: "middle", margin: 0,
    });
    // 内容
    s.addShape(pres.ShapeType.rect, {
      x: 1.4, y, w: 11.4, h: 1.2,
      fill: { color: C.cream }, line: { color: r.col, width: 0.5 },
    });
    s.addText(r.t, {
      x: 1.6, y: y + 0.08, w: 11.0, h: 0.35,
      fontSize: 14, bold: true, color: C.navy, fontFace: F.header, margin: 0,
    });
    s.addText([
      { text: "成因：", options: { bold: true, color: C.accent2 } },
      { text: r.cause,   options: { color: C.charcoal } },
    ], {
      x: 1.6, y: y + 0.42, w: 11.0, h: 0.35,
      fontSize: 11, fontFace: F.body, margin: 0,
    });
    s.addText([
      { text: "应对：", options: { bold: true, color: C.green } },
      { text: r.plan,    options: { color: C.charcoal } },
    ], {
      x: 1.6, y: y + 0.78, w: 11.0, h: 0.35,
      fontSize: 11, fontFace: F.body, margin: 0,
    });
  });

  pageBadge(s, 14, 15);
}

// ============================================================
// SLIDE 15 — 总结 & 讨论
// ============================================================
{
  const s = pres.addSlide();
  bg(s, C.navy);

  // 左侧竖条
  s.addShape(pres.ShapeType.rect, {
    x: 0, y: 0, w: 0.25, h: 7.5,
    fill: { color: C.accent }, line: { color: C.accent },
  });

  s.addText("总结与讨论", {
    x: 0.8, y: 0.5, w: 12, h: 0.8,
    fontSize: 36, bold: true, color: C.white, fontFace: F.header, margin: 0,
  });
  s.addText("用理论回答 V2X 中 “什么必须传”", {
    x: 0.8, y: 1.3, w: 12, h: 0.45,
    fontSize: 16, color: C.teal, fontFace: F.body, italic: true, margin: 0,
  });

  // 三句话总结
  const summary = [
    { n: "1", t: "V2X 协同感知的核心瓶颈是通信带宽" },
    { n: "2", t: "现有方法多为启发式压缩，缺乏信息论下界" },
    { n: "3", t: "我们希望用演绎信源率失真理论刻画 V2X 的 core，并以可训练系统验证" },
  ];
  summary.forEach((it, i) => {
    const y = 2.0 + i * 0.65;
    s.addShape(pres.ShapeType.ellipse, {
      x: 0.8, y, w: 0.5, h: 0.5,
      fill: { color: C.accent }, line: { color: C.accent },
    });
    s.addText(it.n, {
      x: 0.8, y, w: 0.5, h: 0.5,
      fontSize: 16, bold: true, color: C.navy, fontFace: F.header,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText(it.t, {
      x: 1.5, y, w: 11.0, h: 0.5,
      fontSize: 15, color: C.white, fontFace: F.body, valign: "middle", margin: 0,
    });
  });

  // 三个讨论问题
  s.addText("希望获得组会反馈的三个问题", {
    x: 0.8, y: 4.1, w: 12, h: 0.4,
    fontSize: 16, bold: true, color: C.accent, fontFace: F.header, margin: 0,
  });

  const qs = [
    { q: "建模：把 BEV feature 视作 statement 是否合理？closure fidelity 是否适合作为 perception fidelity？" },
    { q: "方法：只实现 R1 是否足以支撑初版实验？是否需要更强的 cross-agent inference module？" },
    { q: "实验：AAAI 论文的最小充分实验集是什么？是否应优先补 DAIR-V2X 真实数据？" },
  ];
  qs.forEach((it, i) => {
    const y = 4.55 + i * 0.55;
    s.addShape(pres.ShapeType.rect, {
      x: 0.8, y, w: 0.15, h: 0.4,
      fill: { color: C.accent }, line: { color: C.accent },
    });
    s.addText([
      { text: `Q${i + 1}    `, options: { color: C.accent, bold: true, fontSize: 13 } },
      { text: it.q, options: { color: C.soft, fontSize: 13 } },
    ], {
      x: 1.15, y, w: 11.7, h: 0.4,
      fontFace: F.body, valign: "middle", margin: 0,
    });
  });

  // 结束语
  s.addShape(pres.ShapeType.rect, {
    x: 0.8, y: 6.4, w: 12.0, h: 0.75,
    fill: { color: C.midnight }, line: { color: C.accent, width: 0.5 },
  });
  s.addText([
    { text: "目标 · ", options: { color: C.accent, bold: true, fontSize: 14 } },
    { text: "不是又提出一个压缩模块，", options: { color: C.soft, fontSize: 14 } },
    { text: "而是为 V2X 协同感知中的 ‘最少通信量’ 提供可解释的理论刻画。",
      options: { color: C.white, fontSize: 14, bold: true } },
  ], {
    x: 1.0, y: 6.4, w: 11.6, h: 0.75,
    fontFace: F.body, valign: "middle", margin: 0,
  });

  s.addText("Thanks · 欢迎讨论", {
    x: 0.8, y: 7.05, w: 12, h: 0.3,
    fontSize: 12, italic: true, color: C.gray, fontFace: F.body, align: "right", margin: 0,
  });
}

// ============================================================
// Save
// ============================================================
pres.writeFile({ fileName: process.argv[2] || "SemRD_V2X_Group_Meeting.pptx" })
    .then(fn => console.log("Saved:", fn));
