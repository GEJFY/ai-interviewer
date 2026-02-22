/**
 * Shared constants for the AI Interview Tool.
 * Matches backend enum definitions in grc_core/enums.py.
 */

// =============================================================================
// Use Case Types (全24タイプ - カテゴリ別)
// =============================================================================

export const USE_CASE_LABELS: Record<string, string> = {
  // Compliance
  compliance_survey: 'コンプライアンス意識調査',
  whistleblower_investigation: '内部通報調査',
  regulation_compliance: '規程遵守確認',
  subcontract_act: '下請法対応',
  privacy_assessment: '個人情報取扱',
  bribery_risk: '贈収賄リスク',

  // Internal Audit
  process_review: '業務プロセスヒアリング',
  transaction_verification: '取引確認',
  anomaly_investigation: '異常取引調査',
  control_evaluation: '統制評価（J-SOX）',
  it_control: 'IT統制評価',
  followup: 'フォローアップ',

  // Risk Management
  risk_assessment: 'リスクアセスメント',
  bcp_evaluation: 'BCP/BCM評価',
  cyber_risk: 'サイバーリスク',
  third_party_risk: '第三者リスク',
  esg_risk: 'ESGリスク',

  // Governance
  board_effectiveness: '取締役会実効性評価',
  internal_control_system: '内部統制システム',
  group_governance: 'グループガバナンス',

  // Knowledge Management
  tacit_knowledge: '暗黙知形式知化',
  handover: '引継ぎ',
  best_practice: 'ベストプラクティス',
};

export interface UseCaseCategory {
  label: string;
  options: Array<{ value: string; label: string }>;
}

export const USE_CASE_CATEGORIES: UseCaseCategory[] = [
  {
    label: 'コンプライアンス',
    options: [
      { value: 'compliance_survey', label: 'コンプライアンス意識調査' },
      { value: 'whistleblower_investigation', label: '内部通報調査' },
      { value: 'regulation_compliance', label: '規程遵守確認' },
      { value: 'subcontract_act', label: '下請法対応' },
      { value: 'privacy_assessment', label: '個人情報取扱' },
      { value: 'bribery_risk', label: '贈収賄リスク' },
    ],
  },
  {
    label: '内部監査',
    options: [
      { value: 'process_review', label: '業務プロセスヒアリング' },
      { value: 'transaction_verification', label: '取引確認' },
      { value: 'anomaly_investigation', label: '異常取引調査' },
      { value: 'control_evaluation', label: '統制評価（J-SOX）' },
      { value: 'it_control', label: 'IT統制評価' },
      { value: 'followup', label: 'フォローアップ' },
    ],
  },
  {
    label: 'リスク管理',
    options: [
      { value: 'risk_assessment', label: 'リスクアセスメント' },
      { value: 'bcp_evaluation', label: 'BCP/BCM評価' },
      { value: 'cyber_risk', label: 'サイバーリスク' },
      { value: 'third_party_risk', label: '第三者リスク' },
      { value: 'esg_risk', label: 'ESGリスク' },
    ],
  },
  {
    label: 'ガバナンス',
    options: [
      { value: 'board_effectiveness', label: '取締役会実効性評価' },
      { value: 'internal_control_system', label: '内部統制システム' },
      { value: 'group_governance', label: 'グループガバナンス' },
    ],
  },
  {
    label: 'ナレッジ管理',
    options: [
      { value: 'tacit_knowledge', label: '暗黙知形式知化' },
      { value: 'handover', label: '引継ぎ' },
      { value: 'best_practice', label: 'ベストプラクティス' },
    ],
  },
];

/** Flat options list for simple selects */
export const USE_CASE_OPTIONS = USE_CASE_CATEGORIES.flatMap((cat) => cat.options);

// =============================================================================
// Report Types
// =============================================================================

export const REPORT_TYPE_LABELS: Record<string, string> = {
  summary: 'インタビュー要約',
  process_doc: '業務記述書',
  rcm: 'RCM（リスクコントロールマトリクス）',
  audit_workpaper: '監査調書',
  survey_analysis: '意識調査分析',
  compliance_report: 'コンプライアンスレポート',
  risk_heatmap: 'リスクヒートマップ',
  gap_analysis: 'ギャップ分析',
};

export const REPORT_TYPE_OPTIONS = Object.entries(REPORT_TYPE_LABELS).map(
  ([value, label]) => ({ value, label })
);
