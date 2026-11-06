import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {Presentation, PresentationFile} from '@oai/artifact-tool';

const buildDir = path.dirname(fileURLToPath(import.meta.url));
const workspaceDir = path.dirname(buildDir);
const SKILL_DIR = process.env.PRESENTATIONS_SKILL_DIR;
if (!SKILL_DIR) throw new Error('Set PRESENTATIONS_SKILL_DIR to the original presentation skill directory.');
const RUNTIME_PYTHON = process.env.RUNTIME_PYTHON;
if (!RUNTIME_PYTHON) throw new Error('Set RUNTIME_PYTHON to the presentation runtime interpreter.');
const {finalizePresentation, applyPresentationChartFont} = await import(pathToFileURL(path.join(SKILL_DIR,'container_tools/artifact_tool_utils.mjs')));
const e = JSON.parse(await fs.readFile(path.join(buildDir,'evidence.json'),'utf8'));
const deck = Presentation.create({slideSize:{width:1280,height:720}});
const discarded = Presentation.create({slideSize:{width:1280,height:720}});
const keepSlides = new Set([1,2,3,4,5,6,7,8,9,11,14,19]);
const includedSlides = new WeakSet();
const color = {navy:'#172A3A', teal:'#126C78', gray:'#51616D', light:'#F5F8F9', orange:'#B75F20'};
const sourceRepo = `https://github.com/vejadu/InterviewCase-Gaming-PC-App/tree/${e.provenance.commit}`;
const slideMap = [];
const nativeTables = [];
const nativeCharts = [];
const f = value => Number(value).toFixed(2);
const p = value => `${Number(value).toFixed(1)}%`;
const interval = row => `${f(row.odds_ratio)} (${f(row.ci_low)}–${f(row.ci_high)})`;
const primary = (outcome,term) => e.primary.find(r=>r.model===outcome+'_usage' && r.term===term);

function text(slide,value,left,top,width,height,size=28,bold=false,fill=color.navy) {
  const shape=slide.shapes.add({geometry:'textbox', name:`text-${slide.shapes.items.length}`,
    position:{left,top,width,height},fill:'none',line:{fill:'none',width:0}});
  shape.text=value;
  shape.text.style={typeface:'Arial',fontSize:size,bold,color:fill};
  return shape;
}
function slide(title,section,sources,notes='') {
  const included = keepSlides.has(slideMap.length+1);
  const s=(included?deck:discarded).slides.add(); s.background.fill='#FFFFFF';
  if(included) includedSlides.add(s);
  text(s,title,64,38,1152,100,42,true);
  text(s,`${section}   ${deck.slides.items.length}`,64,672,1152,24,17,false,color.gray);
  s.speakerNotes.text=`${notes}\n\nEvidence: ${sources.map(name=>e.source_paths[name]??name).join('\n')}\nSource assignment: ${sourceRepo}\nSynthetic example data. Association does not identify a causal effect.`;
  slideMap.push({slide:deck.slides.items.length,title,section,sources,notes,included});
  return s;
}
function table(s,headers,rows,{top=166,left=64,width=1152,height=350,colWidths=null,fontSize=25}={}) {
  const values=[headers,...rows].map(row=>row.map(value=>String(value)));
  const options={rows:values.length,columns:headers.length,left,top,width,height,values};
  if(colWidths) options.columnWidths=colWidths;
  const t=s.tables.add(options);
  t.borders.assign({fill:'#D9E3E8',width:1});
  for(let r=0;r<values.length;r++) for(let c=0;c<headers.length;c++) {
    const cell=t.getCell(r,c);
    cell.fill=r===0?color.navy:(r%2===0?color.light:'#FFFFFF');
    cell.text.style={typeface:'Arial',fontSize,bold:r===0,color:r===0?'#FFFFFF':color.navy};
  }
  if(includedSlides.has(s)) nativeTables.push(deck.slides.items.indexOf(s)+1);
  return t;
}
function chart(s,type,title,categories,series,{top=164,height=382,yTitle='Players (%)',max=1,format='0%',legend=false}={}) {
  series=series.map(item=>({...item,values:item.values.map(value=>Number(value.toPrecision(12)))}));
  const c=s.charts.add(type,{position:{left:64,top,width:1152,height},title,
    titleTextStyle:{fontFamily:'Arial',fontSize:24,color:color.navy},
    categories,series,hasLegend:legend,
    legend:{position:'bottom',textStyle:{fontFamily:'Arial',fontSize:22}},
    barOptions:{direction:'column',grouping:'clustered',gapWidth:90},
    xAxis:{textStyle:{fontFamily:'Arial',fontSize:21,color:color.gray}},
    yAxis:{title:{text:yTitle,textStyle:{fontFamily:'Arial',fontSize:21}},min:0,max,
      numberFormatCode:format,textStyle:{fontFamily:'Arial',fontSize:21,color:color.gray},
      majorGridlines:{fill:'#D9E3E8',width:1}},
    chartFill:'#FFFFFF',plotAreaFill:'#FFFFFF',chartLine:{fill:'none',width:0}});
  applyPresentationChartFont(c,{fontFamily:'Arial'});
  if(includedSlides.has(s)) nativeCharts.push(deck.slides.items.indexOf(s)+1);
  return c;
}
function lines(s,items,{top=176,size=30,gap=98,left=64,width=1152}={}) {
  items.forEach((item,index)=>text(s,item,left,top+index*gap,width,gap-14,size));
}
function note(s,value,top=580) {text(s,value,64,top,1152,74,23,false,color.gray);}

// Leadership presentation: 10 slides, approximately 12 minutes including cover.
{
const s=slide('Contoso AI Gaming Companion','Leadership discussion',[],
  '0:30. Introduce the decision: where should the team investigate retention and upgrade opportunities? This is a synthetic interview exercise, not a real business readout. Slides1–10 support a 10–15 minute leadership discussion.');
text(s,'Growth and product opportunities',64,206,1120,90,52,true,color.teal);
text(s,'300 players, first 60 days',64,340,1100,60,34);
text(s,'Synthetic interview case\nMarch 3–7, 2025 starting cohorts',64,440,1100,96,29,false,color.gray);
}
{
const s=slide('Prioritize a measured onboarding experiment','Leadership discussion',['primary','timing'],
  '1:15. Recommendation is to validate associations on real cohorts and test onboarding, not to operationalize the synthetic estimates. Coaching/Agent use is associated with later retention; Optimizer use has the clearest adjusted conversion association. These do not identify which action causes growth.');
lines(s,[
  'Product: test first-week discovery of Coach and Agent, with retention measured later.',
  'Marketing and sales: test relevant upgrade education around days 7–13.',
  'Engineering: improve exposure, error and billing timestamps before targeting users.',
  'Validate on real cohorts before committing spend or setting growth targets.'
],{size:30,gap:102});
note(s,'All recommendations are testable hypotheses. This synthetic data does not estimate product lift.',600);
}
{
const s=slide('The starting cohort and mandatory outcomes','Leadership discussion',['accounts','conversion','cancellations','cancellation_groups'],
  '1:15. 300 unique day0 players, 60 starting each day March3–7. 232 initially Free and68 initially Paid, day-end plans. 33 initially Free upgraded, leaving101 players ever observed Paid. Sixteen explicit cancellations:13 initially Paid,3 converters. Do not call16/101 a standardized monthly churn rate because Paid exposure varies.');
table(s,['Metric','Observed result','Definition'],[
  ['New accounts','232 Free / 68 Paid','Day-0 end-of-day plan'],
  ['Free-to-Paid','33 / 232 = 14.2%','Initially Free, days 0–59'],
  ['Paid cancellations','16 players','13 initially Paid + 3 converters'],
  ['Ever observed Paid','101 players','68 initially Paid + 33 converters']
],{height:326,colWidths:[300,360,492]});
note(s,'Missing activity is not cancellation. A recorded cancellation must come from explicit billing status.');
}
{
const full=e.weekly_retention.filter(r=>!r.is_partial_week);
const s=slide('Retention declines across the first 60 days','Leadership discussion',['weekly_retention','daily_retention'],
  '1:15. Daily and weekly retention answer different questions. All denominators are original300 day0 players. Last full tenure week days49–55 has137/300=45.7%. Exact day59 has87/300=29.0%. Partial days56–59 has123/300=41.0% and is excluded from the full-week line. Week1 includes day0, making100% mechanical. Full telemetry availability relies on source declaration.');
chart(s,'line','Any activity in each full tenure week',full.map(r=>`W${r.tenure_week}`),[
  {name:'Weekly retention',values:full.map(r=>r.retention_pct/100),line:{fill:color.teal,width:3},marker:{symbol:'circle',size:7}}
]);
note(s,'Last full week: 45.7% (137/300). Exact day 59: 29.0% (87/300). Week 1 includes signup.');
}
{
const s=slide('Coach and Agent use correlate with retention','Leadership discussion',['primary'],
  '1:30. Retention is any activity days28–34. Predictors are days0–6 attempts, successes+errors. Joint model adjusts all3 volumes, active days and starting plan. Displayed OR is per doubling of1+attempts. Coach andAgent BH q=.033, Optimizer q=.217. Pointwise95% intervals. These are conditional odds ratios, not percentage-point changes or causal lift.');
table(s,['First-week feature','Retention OR (95% interval)','Exploratory BH q'],['optimizer','coach','agent'].map(feature=>{
  const r=primary('retention','log2_'+feature); return [feature[0].toUpperCase()+feature.slice(1),interval(r),Number(r.bh_q).toFixed(3)];
}),{height:280,colWidths:[340,522,290]});
text(s,'Optimizer usage has the clearest conversion association',64,488,1152,44,30,true,color.teal);
const r=primary('conversion','log2_optimizer');
note(s,`Conversion OR ${interval(r)}, q=${Number(r.bh_q).toFixed(3)}. Usage ORs are per doubling of (1 + attempts).`,546);
}
{
const errors=e.primary.filter(r=>r.term.includes('_error_10pp'));
const s=slide('Error-rate associations remain inconclusive','Leadership discussion',['primary','correlations'],
  '1:00. All6 volume-adjusted error-rate95% intervals include1. Positive raw error-count correlations can simply reflect more attempts by engaged players. Each error model controls the same feature attempt volume, active days and starting plan for retention. Undefined rate for0attempts is excluded only for that feature; no false zero rates. There is no evidence here that errors help outcomes, nor proof that they are harmless.');
table(s,['Feature error rate','Retention OR (95% interval)','Conversion OR (95% interval)'],['optimizer','coach','agent'].map(feature=>[
  feature[0].toUpperCase()+feature.slice(1),
  interval(errors.find(r=>r.model===`retention_${feature}_errors`)),
  interval(errors.find(r=>r.model===`conversion_${feature}_errors`))
]),{height:290,colWidths:[270,441,441],fontSize:24});
note(s,'Per +10 percentage points in error rate. All intervals include 1. Keep reliability work tied to direct error and user-impact telemetry.');
}
{
const groups=['Weekday','Weekend','Balanced'];
const value=(group,outcome)=>e.segments.find(r=>r.segment==='weekend_preference' && r.group===group && r.outcome===outcome);
const s=slide('Weekend-oriented players have higher raw outcomes','Leadership discussion',['segments','segment_regressions'],
  '1:15. Preference uses first-week active weekend days/2 versus weekdays/5. Retention weekend99/150=66%, weekday53/109=48.6%; conversion weekend22/112=19.6%, weekday5/88=5.7%. Conversion populations exclude initialPaid. Adjusted weekend versusweekday retention OR1.56 CI.91–2.69 q.290, conversion OR3.31 CI1.19–9.23 q.177. No adjusted segment comparison passes5%BH threshold across8 slopes. Differences are exploratory, not a targeting rule.');
chart(s,'bar','Later outcomes by first-week activity preference',groups,[
  {name:'Retained days 28–34',values:groups.map(g=>value(g,'retention').rate_pct/100),fill:color.teal},
  {name:'Converted days 7–59',values:groups.map(g=>value(g,'conversion').rate_pct/100),fill:color.orange}
],{max:0.8,legend:true});
note(s,'Retention n: 109 / 150 / 41. Conversion n: 88 / 112 / 32. Adjusted subgroup evidence is uncertain after multiple comparisons.');
}
{
const s=slide('The largest observed upgrade window is days 7–13','Leadership discussion',['timing','journey'],
  '1:15. Eleven of232 at-riskFree players converted days7–13=4.7%. Median among33converters is24days, range7–43. Later full weeks have2–5conversions. The window with most events is an exploratory sample peak, not a validated optimal marketing intervention time. Conditional denominator isFree atwindowstart. Unequal6dayfirst4daylast windows are marked in labels.');
chart(s,'bar','Conversions / Free players at each window start',e.timing.map(r=>`${r.start_day}–${r.end_day}`),[
  {name:'Conditional conversion',values:e.timing.map(r=>r.conditional_conversion_pct/100),fill:color.teal}
],{max:0.06,yTitle:'Conditional conversion (%)'});
note(s,'Days 7–13: 11/232 (4.7%). Median conversion day among converters: 24. Edge windows have unequal lengths.');
}
{
const s=slide('Actions for product, marketing and engineering','Leadership discussion',['primary','timing'],
  '1:30. Product hypothesis: firstweekCoach/Agent discovery may improve laterretention. Marketing hypothesis: contextualOptimizer value explanation arounddays7–13 may improveupgrades. These require randomizeduserassignment with ITTanalysis. Prespecify day28–34retention and paidconversion to59, monitorerrorrate andcancellations, do prospectivepower calculations from realcohorts. Engineering logsexposure, attempts/errors,signupplanchanges,completecoverage, cancellationevents. No budgets orlift promises basedon syntheticcase.');
table(s,['Team','Proposed next action','Decision evidence needed'],[
  ['Product','Randomize first-week feature discovery','Later retention and error guardrails'],
  ['Marketing / sales','Test contextual upgrade education','Conversion with cancellation guardrails'],
  ['Engineering','Log exposure and billing timestamps','Coverage and event-order validation'],
  ['Data science','Replicate on real cohorts','Stable effects across cohorts and plans']
],{height:350,colWidths:[230,465,457],fontSize:24});
}
{
const s=slide('What the evidence can support','Leadership discussion',['diagnostics','scope'],
  '0:45. Close businesssection. Data are synthetic, no revenue/cost fields, so no ROI model.300players,33upgrades,16cancellations. Do not infer causalimpact from associations or selectbudget basedon ORs. Telemetry completeness source-declared,initialplan dayend. Request approval for a researchandtelemetry plan in a realsetting; no actual externalaction takenhere.');
lines(s,[
  'A useful hypothesis: early feature engagement is associated with later outcomes.',
  'An unresolved decision: which product change actually increases retention or conversion?',
  'A limited sample: 300 players, 33 upgrades and 16 cancellations.',
  'Next step: validate telemetry and run a powered randomized test on real users.'
],{size:31,gap:105});
}

// Technical discussion: 9 slides, approximately 12 minutes.
{
const s=slide('Technical discussion: outcomes and timing','Technical discussion',[],
  '1:15. Slides11–19 support10–15minutes technicaldiscussion. Explain separationofexposureandoutcome,oneindependentplayer. Retentionall300outcome180. Conversion232initialFree33events,noearlyconverters. Day0Paidunknownsamdayordering. Scope population doesnot conditionretention onfutureactivity.');
table(s,['Component','Definition','Population / timing'],[
  ['Predictors','Feature attempts and errors','Days 0–6, one row per player'],
  ['Retention','Any observed activity','Days 28–34, 180/300'],
  ['Conversion','First Paid observation','Days 7–59, 33/232 eligible Free'],
  ['Hazard','Conversion on a day at risk','Days 7–59, player-clustered errors']
],{height:330,colWidths:[240,450,462]});
note(s,'Missing activity does not prove cancellation. First-week predictors precede the modeled outcomes.');
}
{
const s=slide('Cleaning preserves the complete day-0 population','Technical discussion',[],
  '1:00. Source7970rows300players, uniqueplayerday no missinginvalidfields. All29contractchecks passed. Noedits, exclusions orimputation. Originalsourcecolumns retained. Parse dates intonewfields,verifytenure. Roster300. Calendar18000 includes10030constructedrowsonly, unknownplan/status/counts. All20preparationreconciliationchecks passed. Audits rule summary,102800addedfields/calendarrows, source-rowlineage andhash. Newanalysis aggregationauditseparate.');
table(s,['Output','Rows','Preservation / purpose'],[
  ['Observed activity','7,970','Every source row and original value retained'],
  ['Player roster','300','One validated day-0 anchor per player'],
  ['Retention calendar','18,000','60 tenure days per original player'],
  ['Constructed calendar rows','10,030','No observed activity, unknown billing/counts']
],{height:320,colWidths:[380,170,602]});
note(s,'29 source-contract checks and 20 preparation checks passed. Every addition has an audit trail.');
}
{
const s=slide('Raw correlation differs from conditional association','Technical discussion',['correlations','primary'],
  '1:00. Spearmanrankbinaryoutcomeassociations.4999permutationsseed20261105;BH18correlations. Error-rateundefinedfor0attemptsnotimputed. RawpositiveOptimizererrorcount conversionrho.182 q.014; adjustforvolume errorOR1.23CI.58–2.65, no evidencebenefitoferrors. All primaryusagepositive. pvaluesforindependencenotconfounderadjusted. SciPy docs permutationrecommended smallsample, ownrandomization implementationverifiedrho SciPy.');
table(s,['Feature attempts','Retention Spearman rho','Conversion Spearman rho'],['optimizer','coach','agent'].map(feature=>[
  feature[0].toUpperCase()+feature.slice(1),
  Number(e.correlations.find(r=>r.feature===feature&&r.measurement==='attempts'&&r.outcome==='retention').spearman_rho).toFixed(3),
  Number(e.correlations.find(r=>r.feature===feature&&r.measurement==='attempts'&&r.outcome==='conversion').spearman_rho).toFixed(3)
]),{height:275,colWidths:[370,391,391]});
note(s,'4,999 outcome-label permutations. BH adjustment across 18 correlations. Raw error counts can proxy for greater use.');
}
{
const s=slide('Separate logistic regressions for the two outcomes','Technical discussion',['primary','diagnostics'],
  '1:45. logitP(retained)=intercept + log2(1+optimizerattempts)+log2(1+coachattempts)+log2(1+agentattempts)+activedays+initialPaid. conversion samewithoutinitialPaidallFree. HC1. sixretentionparameters,fiveconversionparameters.33events/4slopes8.25only exploratorynot10rulepassproof. VIFmax5.28usagecorrelation limitsfeatureattribution. Errorfeaturemodel additionalrate10ppwithownvolume controls. Pointwise95%CI;BH12primaryslopes. Oddsnotprobabilities. Nooutofsampleclaims.');
text(s,'Retention',64,170,1152,48,32,true,color.teal);
text(s,'logit P = feature volumes + active days + initial Paid plan',64,224,1152,64,30);
text(s,'Conversion',64,324,1152,48,32,true,color.teal);
text(s,'logit P = feature volumes + active days',64,378,1152,64,30);
note(s,'Feature volumes: log2(1 + first-week attempts). HC1 uncertainty. 95% pointwise intervals and BH q-values for 12 primary slopes.',510);
}
{
const s=slide('Sensitivity checks retain the main usage directions','Technical discussion',['sensitivity','hazard_sensitivity'],
  '1:30. SeparatefeaturemodelsretainpositiveCoachAgentretention andOptimizerconversiondirections. InitiallyFreeonlyretentionCoach1.61Agent1.65,Optimizer1.17CIincludes1. Morefeaturesandsmallsamplechange magnitudesso do notrank causalcontributions. Comparejointvsfeature-specificORvaluesnotindependentestimates. All21modelconverged. Centeredquadraticlogtenurehazardsensitivity available,featuredirectionspositive. FullVIFdiagnosticssaved.');
const rows=[];
for(const outcome of ['retention','conversion'])for(const feature of ['optimizer','coach','agent']){
  const joint=e.sensitivity.find(r=>r.specification===outcome+'_usage'&&r.feature===feature);
  const single=e.sensitivity.find(r=>r.specification===outcome+'_'+feature+'_single_usage'&&r.feature===feature);
  rows.push([outcome[0].toUpperCase()+outcome.slice(1),feature,f(joint.odds_ratio),f(single.odds_ratio)]);
}
table(s,['Outcome','Feature','Joint usage OR','Single-feature OR'],rows,{height:370,colWidths:[300,280,286,286],fontSize:24});
note(s,'All signs remain positive. Retention among initially Free players also retains the Coach and Agent signals.',578);
}
{
const s=slide('Subgroup estimates remain exploratory','Technical discussion',['segment_regressions','scope','segments'],
  '1:15. Activitypreferenceweekendactivedays/2vsweekdays/5,dominantfeatureaverageattempts/dailyplanlimit,allfirstweek. Retentionweekendvsweekday OR1.56CI.91–2.69q.290. ConversionOR3.31CI1.19–9.23q.177. No8groupcontrastspassBH. Balancedfeaturegroup3players allretained causednonfiniteSE originalmodel. Revisionexclude categoriesn<10fromadjustedfeaturemodelonly,retention297events177;conversion230events32. Rawtablekeepallgroups. Selectionbynnotfavourableresults;revisiondocumented.');
const weekendRows=e.segment_regressions.filter(r=>r.term.endsWith('[T.Weekend]'));
table(s,['Weekend vs weekday','Adjusted OR (95% interval)','BH q'],weekendRows.map(r=>[
  r.model.startsWith('retention')?'Retention':'Conversion',interval(r),Number(r.bh_q).toFixed(3)
]),{height:228,colWidths:[350,530,272]});
lines(s,['Feature-preference intervals overlap. Raw ranks do not identify a best feature.',
  'Balanced feature group: 3 players. Retained descriptively, excluded from adjusted group models.'],{top:440,size:27,gap:90});
}
{
const s=slide('Conversion hazard uses the correct at-risk denominator','Technical discussion',['hazard','timing','hazard_sensitivity'],
  '1:30. Construct11162persondays232players33events. KeepinactiveFreeplayersatriskuntilconversionor59,noFreecancellationinsource. logitdailyconversion=logtenure+3fixedfirstweekfeaturelogs+activedays. Clusterbyplayer,repeateddaysnotindependent. Conditionaldailyoddsnot53dayrisk.33events5slopes6.6events/slope. Modelassumedsmoothbaseline,quadraticcenteredlogtimecheckprespecifiedbeforefit. Displayclustered95%CIunadjustedexploratory,notprimaryBHfamily.');
table(s,['First-week feature','Daily conversion OR (95% interval)'],['optimizer','coach','agent'].map(feature=>[
  feature[0].toUpperCase()+feature.slice(1),interval(e.hazard.find(r=>r.term==='log2_'+feature))
]),{height:270,colWidths:[460,692]});
note(s,'11,162 at-risk player-days, 232 players, 33 events. Clustered by player. Baseline log tenure; quadratic sensitivity also fitted.');
}
{
const s=slide('Journeys describe eventual converters','Technical discussion',['journey'],
  '1:00. All33convertersupgradeafteratleastday7,eachhas7dayprewindow.25/33active7daysbefore vs28/33active1daybefore. Meansfeatureattemptscomputedamongactiverows,notallcalendarrows. Do not inferpreupgradesurgecausesupgrade. Wouldneedmatchedrisksetnonconvertersatrelevanttenureandtime,notfuture-outcomeselectiontoinfer causes. Upgrade-dayusageexcludedendofdaysnapshot.');
chart(s,'line','Observed activity in the week before upgrade',e.journey.map(r=>String(r.relative_day)),[
  {name:'Active among converters',values:e.journey.map(r=>r.active_pct/100),line:{fill:color.teal,width:3},marker:{symbol:'circle',size:7}}
],{yTitle:'Active / eligible converters (%)'});
note(s,'33 eventual converters. Relative day 0 is excluded. Feature means in the notebook use active observed days only.');
}
{
const s=slide('Validation, evaluation and code walkthrough','Technical discussion',['diagnostics'],
  '1:30. Walkthroughanalysis.ipynb andanalysis.py. Cleaninginputsdatainterview_question unchangedSHA. All29contract20prep11mandatorychecks. Newchecksstdlibsourcetotals/outcomes,allhazardrisksets,SpearmanSciPy,independentSciPyBFGS2mainlogitscoefdiff<1e-4,all21fitsconvergednowarnings. Noheldoutpredictionclaim. Forpredictiveuseprotectplayer-levelsplitbeforelearnedpreprocessing,comparebaseprevalence,testcalibrationdiscriminationlatercohorts. DSactionsrealcohortsrobustnesscohortandplan,experimentpower;engactions signupplanbillingtimestamps,errorseveritylatencyandexposure. Sourcefilesandtablesrelative.');
lines(s,[
  'Reproduce: restart the project kernel and run analysis.ipynb, or run create_notebook.py.',
  'Verify: source-ledger counts, risk sets, correlations and independent main-model fits.',
  'Review: formula, cohort membership, convergence, intervals, collinearity and sensitivity.',
  'Before deployment: use real cohorts, a player-level holdout and randomized product tests.'
],{size:29,gap:101});
note(s,'Code and exact versions are supplied with the notebook. Analysis.py is exported from the same notebook code.',596);
}

const conciseNotes = [
  'Introduce this synthetic interview exercise. Slides 1–9 support the leadership discussion. Slides 10–12 support a technical discussion together with the notebook code walkthrough. The decision is where to investigate retention and upgrade opportunities.',
  'These recommendations are hypotheses for real-world testing. Coach and Agent usage have positive adjusted retention associations. Optimizer usage has the clearest adjusted conversion association. Validate on real cohorts before changing spend or product policy.',
  'Count each day-0 player once. Initial plan is observed at the end of day 0. The 33 upgrades increase the ever-Paid roster to 101. The 16 cancellations include 13 initially Paid players and 3 converters. Unequal Paid exposure prevents interpreting this as standardized monthly churn.',
  'Weekly retention means any activity in the specified tenure week. Daily retention means activity on that exact day. Both use the original 300 players. The partial final week is excluded from this full-week line. Week 1 is mechanically 100% because it includes day 0.',
  'Predictors are first-week attempts. Retention is activity during days 28–34. Models adjust for all three feature volumes, active days and initial plan where applicable. Odds ratios are per doubling of 1 plus attempts. These are associations, not percentage-point effects or causal lift.',
  'Error rates divide errors by attempts. Each model controls its own feature volume and general activity. All six adjusted intervals include 1. Players with zero attempts have undefined rates and are excluded only from that feature model. This does not prove errors are harmless.',
  'Weekend preference compares active weekend days divided by 2 with active weekdays divided by 5. Retention populations are 109, 150 and 41. Conversion populations are 88, 112 and 32. Adjusted segment comparisons are uncertain after multiple-comparison adjustment.',
  'Eleven of 232 at-risk Free players upgraded during days 7–13. This is the largest observed grouped percentage. Among 33 eventual converters, median upgrade tenure is 24 days. Sparse events limit peak comparisons. An observed peak does not establish the best intervention date.',
  'Product can test early feature discovery. Marketing can test contextual upgrade education. Engineering should log exposure, feature attempts, severity and billing events precisely. Data science should replicate on real cohorts and calculate prospective experiment power. Use randomized assignment and intent-to-treat outcomes.',
  'Feature predictors use days 0–6. Retention is any activity during days 28–34. Conversion eligibility requires initially Free players who have not converted by day 6. No first-week conversions occur in this file. Missing activity is not cancellation. Coverage completeness relies on the source statement.',
  'Explain the logistic formulas in the notebook. Feature volumes are log2 of 1 plus attempts. HC1 uncertainty treats players as independent. The 12 primary feature slopes use Benjamini–Hochberg q-values. Thirty-three conversion events limit precision. Error models add the feature error rate with volume adjustment.',
  'Walk through analysis.ipynb or its exact code export, analysis.py. Source-ledger checks verify totals, outcomes and risk sets. Independent SciPy optimizers match both primary usage regressions. All 21 final fits converged. Tiny balanced feature groups remain descriptive only. Prediction would require player-level holdout evaluation; causal product decisions require randomized tests.'
];
const finalMap = slideMap.filter(item=>item.included);
for(let i=0;i<finalMap.length;i++){
  finalMap[i].notes=conciseNotes[i];
  deck.slides.items[i].speakerNotes.text=conciseNotes[i]+'\n\nEvidence:\n'+finalMap[i].sources.map(name=>e.source_paths[name]??name).join('\n')+'\nAssignment: '+sourceRepo+'\nSynthetic data. Association does not establish causality.';
}
await fs.writeFile(path.join(workspaceDir,'slide_evidence.json'),JSON.stringify(finalMap,null,2));
await fs.mkdir(path.join(workspaceDir,'previews'),{recursive:true});
await fs.mkdir(path.join(workspaceDir,'output'),{recursive:true});
const candidatePath=path.join(buildDir,'candidate.pptx');
await (await PresentationFile.exportPptx(deck)).save(candidatePath);
console.log(`Draft exported: ${deck.slides.items.length} slides`);

// Render every authored slide for individual visual review.
for(let i=0;i<deck.slides.items.length;i++){
  const blob=await deck.export({slide:deck.slides.items[i],format:'png',scale:1});
  await fs.writeFile(path.join(workspaceDir,'previews',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await blob.arrayBuffer()));
  console.log(`Rendered ${i+1}`);
}
const FINAL_PPTX=path.join(workspaceDir,'output','contoso_growth_analysis.pptx');
const result=await finalizePresentation({
  workspaceDir,candidatePath,finalPath:FINAL_PPTX,pythonExecutable:RUNTIME_PYTHON,
  integrityValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',
    ...nativeTables.flatMap(n=>['--require-native-table-slide',String(n)])],
  requiredNativeTableOwnerSlides:nativeTables,requiredNativeChartOwnerSlides:nativeCharts,
  explicitTotalSlideCount:12,materializeLiteralChartWorkbooks:true,
  fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,
  receiptPath:path.join(buildDir,'validation.json'),
});
console.log(JSON.stringify({finalPath:FINAL_PPTX,result}));
