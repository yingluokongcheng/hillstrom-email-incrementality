from pathlib import Path
import argparse, html, json
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
LABELS={'Mens E-Mail':'男装邮件','Womens E-Mail':'女装邮件','No E-Mail':'不发邮件',
        'Overall':'总体','Urban':'城市 Urban','Suburban':'郊区 Suburban','Rural':'乡村 Rural'}

def table(df):
    return '<div class="table-wrap">'+df.to_html(index=False,escape=True,border=0,float_format=lambda x:f'{x:.4f}')+'</div>'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--reports',type=Path,default=ROOT/'reports')
    args=parser.parse_args(); folder=args.reports
    load=lambda name:pd.read_csv(folder/(name+'.csv'))
    result=json.loads((folder/'audit_results.json').read_text(encoding='utf-8'))
    source=json.loads((ROOT/'data/raw/source_manifest.json').read_text(encoding='utf-8'))
    groups=load('group_counts').set_index('segment').loc[['Mens E-Mail','Womens E-Mail','No E-Mail']].reset_index()
    groups['segment']=groups.segment.map(LABELS)
    groups['allocation_pct']=groups.allocation_pct.map(lambda x:f'{x:.3f}%')
    groupview=groups[['segment','n','allocation_pct','purchases','nonpurchases']].rename(columns={
        'segment':'分配组','n':'样本数','allocation_pct':'分配比例','purchases':'购买数（稀疏检查）','nonpurchases':'未购买数'})
    rg=load('region_group_counts')
    regionview=[]
    for region in ['Urban','Suburban','Rural']:
        subset=rg[rg.region.eq(region)].set_index('segment')
        regionview.append({'地区':LABELS[region],**{LABELS[g]+'样本':int(subset.loc[g,'n']) for g in ['Mens E-Mail','Womens E-Mail','No E-Mail']},
                           '最少单组购买数':int(subset.purchases.min()),'合计':int(subset.n.sum())})
    power=load('scenario_power'); mde=load('scenario_mde'); requirements=load('scenario_required_n')
    summary=[]
    for pop in ['Overall','Urban','Suburban','Rural']:
        for base in [.005,.01,.02]:
            pp=power[(power.population==pop)&(power.baseline_scenario==base)&(power.delta_scenario==.001)]
            mm=mde[(mde.population==pop)&(mde.baseline_scenario==base)&(mde.target_power==.8)]
            nn=mde[(mde.population==pop)&(mde.baseline_scenario==base)&(mde.target_power==.9)]
            summary.append({'范围':LABELS[pop],'假设基线':f'{100*base:.1f}%',
              '检出+0.10pp的功效':f'{pp.power_approx.min()*100:.1f}–{pp.power_approx.max()*100:.1f}%',
              '80%功效 MDE（pp）':f'{mm.mde_probability.min()*100:.3f}–{mm.mde_probability.max()*100:.3f}',
              '90%功效 MDE（pp）':f'{nn.mde_probability.min()*100:.3f}–{nn.mde_probability.max()*100:.3f}'})
    sample_req=requirements[(requirements.baseline_scenario==.01)&(requirements.delta_scenario==.001)][['target_power','n_per_arm_equal','n_three_arms_equal']].copy()
    sample_req['target_power']=sample_req.target_power.map(lambda p:f'{p:.0%}')
    sample_req=sample_req.rename(columns={'target_power':'目标功效（每项比较）','n_per_arm_equal':'每组约需人数','n_three_arms_equal':'三组等额合计'})
    quality=pd.DataFrame([
        ['缺失单元格',result['missing_cells'],'12个字段及各分组均检查'],
        ['非法值/区间/结果逻辑检查命中',result['anomaly_flags'],'详细检查项见下方明细'],
        ['相同行涉及的行数',result['identical_rows_all_members'],'不等于已证实的重复客户'],
        ['相同组合数',result['identical_row_patterns'],'每种组合至少出现两次'],
        ['每种组合只留首行时会删掉的行数',result['identical_rows_excess'],'只是计数；本项目未去重'],
        ['相同行中 history=29.99 的行数',result['identical_rows_with_history_29_99'],'共同取值可使不同客户记录相同，不能据此证明身份'],
        ['删除/填补行数',f"{result['rows_dropped']} / {result['rows_imputed']}",'原始64,000行完整保留'],
    ],columns=['检查','结果','解释'])
    detail_sections=''
    for name,title in [('missingness','全部字段缺失'),('missingness_by_group','按组缺失'),('anomaly_summary','全部异常规则'),
                       ('numeric_ranges','数值范围'),('region_group_counts','地区×组全部计数'),('baseline_balance','完整分组前平衡'),
                       ('scenario_power','全部功效情景'),('scenario_mde','全部MDE情景'),('scenario_required_n','全部样本量情景')]:
        detail_sections+=f'<details><summary>{title} · <a href="{name}.csv">CSV</a></summary>{table(load(name))}</details>'
    blockers='；'.join(result['structural_blockers']) or '未触发预设的结构性停止规则；仍需用户审计确认'
    body=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hillstrom 数据审计与样本支撑</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f3f6fa;color:#1e2b3b;font:16px/1.8 system-ui,"Microsoft YaHei",sans-serif}}
main{{max-width:1120px;margin:36px auto;padding:0 24px 60px}}header{{background:#152f47;color:white;padding:32px;border-radius:16px}}
h1{{font-size:30px;margin:8px 0}}h2{{margin-top:34px;font-size:22px}}p{{margin:12px 0}}.eyebrow{{font-size:13px;letter-spacing:1px;color:#bdd5e8}}
.callout{{padding:20px 24px;background:#fff5d9;border-left:5px solid #b57e15;border-radius:8px;margin:24px 0}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:20px 0}}.card{{background:white;padding:18px;border-radius:10px;border:1px solid #dce4ed}}
.big{{display:block;font-size:26px;font-weight:700;color:#17636b}}.table-wrap{{overflow-x:auto;background:white;border:1px solid #dce4ed;border-radius:9px;margin:14px 0}}
table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:10px 12px;text-align:left;border-bottom:1px solid #e7edf2;white-space:nowrap}}
th{{background:#eaf1f7;color:#21415a}}tr:last-child td{{border-bottom:0}}a{{color:#126b87}}code{{overflow-wrap:anywhere;white-space:normal;font-size:13px}}
details{{background:white;padding:12px 16px;margin:10px 0;border-radius:8px;border:1px solid #dce4ed}}summary{{cursor:pointer;font-weight:600}}
.note{{font-size:14px;color:#526275}}footer{{margin-top:30px;border-top:1px solid #cbd6e1;padding-top:16px}}
@media(max-width:700px){{.cards{{grid-template-columns:repeat(2,1fr)}}main{{padding:0 12px}}header{{padding:20px}}h1{{font-size:25px}}}}
</style></head><body><main>
<header><div class="eyebrow">HILLSTROM · LOCAL REPRODUCIBLE AUDIT · 2026-10-17</div><h1>数据可以支持什么程度的结论？</h1>
<p>固定计划 v1 · 总体增量为主 / 地区探索为辅<br>当前阶段：审计完成，等待确认；尚未运行邮件效果分析。</p></header>
<div class="cards"><div class="card"><span class="big">{result['n']:,}</span>原始记录</div><div class="card"><span class="big">{result['missing_cells']}</span>缺失单元格</div>
<div class="card"><span class="big">{result['srm']['p']:.4f}</span>整体 SRM p 值</div><div class="card"><span class="big">+0.10 pp</span>固定情景基准</div></div>
<div class="callout"><b>结论：可在来源与身份限制下继续固定总体分析，但样本不足以稳定识别 +0.10 个百分点的小提升。</b>
<p>在假设基线为1%、每项双侧 α=0.025 时，总体对该提升的近似功效约11%，80%功效所需效果约+0.32个百分点。地区更弱，应维持探索定位。此处是预设情景规划，不是邮件实际效果。</p></div>
<h2>01 / 分组比例与分组前平衡</h2>{table(groupview)}
<p>按1∶1∶1检查：χ²={result['srm']['chi2']:.6f}，自由度2，p={result['srm']['p']:.6f}，未触发预设 p&lt;0.001 阈值。
分组前变量最大 |SMD|={result['baseline_max_abs_smd']:.4f}，超过0.1的比较数为{result['baseline_features_abs_smd_over_0_1']}。这未发现明显分配失衡，但不能证明原始随机化、身份独立性或名册完整性。</p>
<p class="note">购买数仅用于稀疏检查。本轮已查看分组结果计数，因此后续不能称为盲态分析；没有计算购买率差、效果p值或邮件优劣排名。</p>
<h2>02 / 缺失、异常与重复记录风险</h2>{table(quality)}
<p>全部购买/未购买格计数在总体最少为{result['minimum_overall_outcome_cell']}，地区最少为{result['minimum_region_outcome_cell']}，均超过预设10的稀疏阈值。
但“可计算常规统计量”不等于“有足够功效识别小效果”。</p>
<p><b>7,634行涉及完全相同的12字段组合，未删除。</b>其中7,570行历史消费额为29.99。共同价格、粗粒度特征和二元结果可能产生相同行；没有客户ID，无法认定是重复抽样，也无法确认都是独立客户。
所有功效规划均以行代表独立客户为条件；如果实际存在重复客户，精度可能被高估。未用去重后的样本另跑结果。</p>
<p>地区原值为 <code>Surburban</code>，涉及28,776行；仅派生展示名称为 <code>Suburban</code>。原始文件未改。这个变量只是城乡分类，无法用于具体城市或文化解释。</p>
<p><a href="identical_rows.csv">相同行清单（含CSV行号）</a> · <a href="anomaly_rows.csv">逻辑异常行清单</a> · <a href="region_alias.csv">名称映射记录</a></p>
<h2>03 / 总体与地区样本覆盖</h2>{table(pd.DataFrame(regionview))}
<h2>04 / 样本量能否支撑 +0.10 个百分点？</h2>
<p>下表覆盖预先固定的全部三种基线情景。区间表示两项邮件—对照比较之间的范围，不是置信区间。pp=百分点；MDE=达到指定功效所需的最小可检出正向差异。</p>
{table(pd.DataFrame(summary))}
<p>所有情景使用每项双侧 α=0.025，正态近似 score 功效公式；不使用实际购买率或观察效果作为输入。
地区使用同一阈值作精度参照，不赋予六项地区比较确认性地位；功效也不等于两项检验同时成功的概率。</p>
<p>如果未来实验的基线确为1%，要对+0.10pp达到下列功效，三组等额分配约需要：</p>{table(sample_req)}
<p>这是未来规划情景，不建议为了本项目“凑人数”，也不会过采样、合并地区或更换主指标追求显著。若后续区间跨零且包含有意义提升，应写“证据不足”；不能写成“邮件无效”或“当地客户不敏感”。</p>
<h2>05 / 来源与可验证边界</h2>
<p>原作者CSV地址因证书验证失败未取得，未关闭TLS验证。使用<a href="https://www.uplift-modeling.com/en/latest/api/datasets/fetch_hillstrom.html">scikit-uplift文档副本</a>；压缩包MD5与文档一致。
没有与作者原始字节对账。<a href="https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html">原始研究说明</a>提供随机分组与两周观察背景。</p>
<p>CSV SHA-256：<code>{result['raw_sha256']}</code><br>来源、下载时间、尝试记录与下载前计划哈希见 <a href="../data/raw/source_manifest.json">source_manifest.json</a>。</p>
<p>缺少客户ID、分配/送达日志和时间戳，无法独立核验重复身份、投递执行、每人观察窗口及原始完整名册。无成本、利润和退订数据；+0.10pp不是盈利门槛。</p>
<h2>06 / 审计判定与下一步</h2><p><b>{html.escape(blockers)}</b></p>
<p>建议保留原计划：总体做两项固定比较；三个地区只作带不确定性的探索。必须携带相同行及来源限制，并接受可能无法排除小幅有益效果。用户确认审计前，不执行效果分析。</p>
<h2>07 / 完整可追溯明细</h2>{detail_sections}
<footer><p>本地运行：项目目录执行 <code>.venv\\Scripts\\python.exe scripts/run_offline.py</code>，生成本报告与CSV/JSON。首次安装或重新下载需网络，缓存齐备后无需云平台。
参见 <a href="../README.zh-CN.md">中文复现说明</a>、<a href="../docs/PLAN_v1.md">已确认计划</a>、<a href="../docs/AUDIT_METHODS.md">实现口径</a>、<a href="verification.json">复现验证记录</a>。</p></footer>
</main></body></html>'''
    (folder/'Hillstrom数据审计.html').write_text(body,encoding='utf-8')
    print('Built Hillstrom audit report.')

if __name__=='__main__':
    main()
