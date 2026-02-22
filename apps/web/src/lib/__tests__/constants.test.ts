/**
 * 定数定義のテスト
 * テスト対象: apps/web/src/lib/constants.ts
 */

import {
  USE_CASE_LABELS,
  USE_CASE_CATEGORIES,
  USE_CASE_OPTIONS,
  REPORT_TYPE_LABELS,
  REPORT_TYPE_OPTIONS,
} from '../constants';

describe('USE_CASE_LABELS', () => {
  it('23種類のユースケースが定義されていること', () => {
    expect(Object.keys(USE_CASE_LABELS)).toHaveLength(23);
  });

  it('コンプライアンスカテゴリのラベルが含まれること', () => {
    expect(USE_CASE_LABELS.compliance_survey).toBe('コンプライアンス意識調査');
    expect(USE_CASE_LABELS.whistleblower_investigation).toBe('内部通報調査');
    expect(USE_CASE_LABELS.bribery_risk).toBe('贈収賄リスク');
  });

  it('内部監査カテゴリのラベルが含まれること', () => {
    expect(USE_CASE_LABELS.process_review).toBe('業務プロセスヒアリング');
    expect(USE_CASE_LABELS.control_evaluation).toBe('統制評価（J-SOX）');
    expect(USE_CASE_LABELS.it_control).toBe('IT統制評価');
  });

  it('リスク管理カテゴリのラベルが含まれること', () => {
    expect(USE_CASE_LABELS.risk_assessment).toBe('リスクアセスメント');
    expect(USE_CASE_LABELS.cyber_risk).toBe('サイバーリスク');
    expect(USE_CASE_LABELS.esg_risk).toBe('ESGリスク');
  });

  it('ガバナンスカテゴリのラベルが含まれること', () => {
    expect(USE_CASE_LABELS.board_effectiveness).toBe('取締役会実効性評価');
    expect(USE_CASE_LABELS.internal_control_system).toBe('内部統制システム');
  });

  it('ナレッジ管理カテゴリのラベルが含まれること', () => {
    expect(USE_CASE_LABELS.tacit_knowledge).toBe('暗黙知形式知化');
    expect(USE_CASE_LABELS.handover).toBe('引継ぎ');
    expect(USE_CASE_LABELS.best_practice).toBe('ベストプラクティス');
  });
});

describe('USE_CASE_CATEGORIES', () => {
  it('5カテゴリが定義されていること', () => {
    expect(USE_CASE_CATEGORIES).toHaveLength(5);
  });

  it('各カテゴリにlabelとoptionsがあること', () => {
    USE_CASE_CATEGORIES.forEach((category) => {
      expect(category.label).toBeTruthy();
      expect(Array.isArray(category.options)).toBe(true);
      expect(category.options.length).toBeGreaterThan(0);
    });
  });

  it('カテゴリ名が正しいこと', () => {
    const categoryNames = USE_CASE_CATEGORIES.map((c) => c.label);
    expect(categoryNames).toEqual([
      'コンプライアンス',
      '内部監査',
      'リスク管理',
      'ガバナンス',
      'ナレッジ管理',
    ]);
  });

  it('各optionにvalueとlabelがあること', () => {
    USE_CASE_CATEGORIES.forEach((category) => {
      category.options.forEach((option) => {
        expect(option.value).toBeTruthy();
        expect(option.label).toBeTruthy();
      });
    });
  });
});

describe('USE_CASE_OPTIONS', () => {
  it('全カテゴリのオプションがフラット化されていること', () => {
    const totalOptions = USE_CASE_CATEGORIES.reduce(
      (sum, cat) => sum + cat.options.length,
      0
    );
    expect(USE_CASE_OPTIONS).toHaveLength(totalOptions);
  });

  it('各optionのvalueがUSE_CASE_LABELSに存在すること', () => {
    USE_CASE_OPTIONS.forEach((option) => {
      expect(USE_CASE_LABELS[option.value]).toBeDefined();
    });
  });
});

describe('REPORT_TYPE_LABELS', () => {
  it('8種類のレポートタイプが定義されていること', () => {
    expect(Object.keys(REPORT_TYPE_LABELS)).toHaveLength(8);
  });

  it('基本レポートタイプが含まれること', () => {
    expect(REPORT_TYPE_LABELS.summary).toBe('インタビュー要約');
    expect(REPORT_TYPE_LABELS.process_doc).toBe('業務記述書');
    expect(REPORT_TYPE_LABELS.rcm).toBe('RCM（リスクコントロールマトリクス）');
    expect(REPORT_TYPE_LABELS.audit_workpaper).toBe('監査調書');
  });

  it('新規追加レポートタイプが含まれること', () => {
    expect(REPORT_TYPE_LABELS.survey_analysis).toBe('意識調査分析');
    expect(REPORT_TYPE_LABELS.compliance_report).toBe('コンプライアンスレポート');
    expect(REPORT_TYPE_LABELS.risk_heatmap).toBe('リスクヒートマップ');
    expect(REPORT_TYPE_LABELS.gap_analysis).toBe('ギャップ分析');
  });
});

describe('REPORT_TYPE_OPTIONS', () => {
  it('REPORT_TYPE_LABELSと同じ数のオプションがあること', () => {
    expect(REPORT_TYPE_OPTIONS).toHaveLength(Object.keys(REPORT_TYPE_LABELS).length);
  });

  it('各optionにvalueとlabelがあること', () => {
    REPORT_TYPE_OPTIONS.forEach((option) => {
      expect(option.value).toBeTruthy();
      expect(option.label).toBeTruthy();
      expect(REPORT_TYPE_LABELS[option.value]).toBe(option.label);
    });
  });
});
