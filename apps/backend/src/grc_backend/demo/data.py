"""Demo data definitions for AI Interview Tool.

架空企業「テクノファイナンス株式会社」を使用した
GRC Advisory AIヒアリングシステムのデモデータ。
"""

from datetime import UTC, date, datetime, timedelta

# --- 固定UUID (再現性のため) ---

# Organization
ORG_ID = "d0000000-0000-0000-0000-000000000001"

# Users
USER_ADMIN_ID = "u0000000-0000-0000-0000-000000000001"
USER_MANAGER_ID = "u0000000-0000-0000-0000-000000000002"
USER_INTERVIEWER_ID = "u0000000-0000-0000-0000-000000000003"
USER_VIEWER_ID = "u0000000-0000-0000-0000-000000000004"

# Projects
PROJECT_JSOX_ID = "p0000000-0000-0000-0000-000000000001"
PROJECT_COMPLIANCE_ID = "p0000000-0000-0000-0000-000000000002"
PROJECT_CYBER_ID = "p0000000-0000-0000-0000-000000000003"

# Templates
TPL_CONTROL_EVAL_ID = "t0000000-0000-0000-0000-000000000001"
TPL_PROCESS_REVIEW_ID = "t0000000-0000-0000-0000-000000000002"
TPL_COMPLIANCE_ID = "t0000000-0000-0000-0000-000000000003"
TPL_CYBER_RISK_ID = "t0000000-0000-0000-0000-000000000004"

# Tasks
TASK_PURCHASE_ID = "k0000000-0000-0000-0000-000000000001"
TASK_SALES_ID = "k0000000-0000-0000-0000-000000000002"
TASK_IT_CONTROL_ID = "k0000000-0000-0000-0000-000000000003"
TASK_COMP_MGR_ID = "k0000000-0000-0000-0000-000000000004"
TASK_COMP_STAFF_ID = "k0000000-0000-0000-0000-000000000005"
TASK_CYBER_IT_ID = "k0000000-0000-0000-0000-000000000006"
TASK_CYBER_EXEC_ID = "k0000000-0000-0000-0000-000000000007"

# Interviewees
IEE_TAKAHASHI_ID = "e0000000-0000-0000-0000-000000000001"
IEE_WATANABE_ID = "e0000000-0000-0000-0000-000000000002"
IEE_ANON1_ID = "e0000000-0000-0000-0000-000000000003"
IEE_ANON2_ID = "e0000000-0000-0000-0000-000000000004"
IEE_KOBAYASHI_ID = "e0000000-0000-0000-0000-000000000005"

# Interviews
ITV_PURCHASE_ID = "i0000000-0000-0000-0000-000000000001"
ITV_SALES_ID = "i0000000-0000-0000-0000-000000000002"
ITV_IT_CONTROL_ID = "i0000000-0000-0000-0000-000000000003"
ITV_COMP_MGR_ID = "i0000000-0000-0000-0000-000000000004"
ITV_CYBER_IT_ID = "i0000000-0000-0000-0000-000000000005"

# Reports
RPT_PURCHASE_PROC_ID = "r0000000-0000-0000-0000-000000000001"
RPT_PURCHASE_RCM_ID = "r0000000-0000-0000-0000-000000000002"
RPT_SALES_WP_ID = "r0000000-0000-0000-0000-000000000003"
RPT_COMP_SURVEY_ID = "r0000000-0000-0000-0000-000000000004"
RPT_CYBER_SUMMARY_ID = "r0000000-0000-0000-0000-000000000005"

# Knowledge Items
KN_PURCHASE_ID = "n0000000-0000-0000-0000-000000000001"
KN_SALES_ID = "n0000000-0000-0000-0000-000000000002"
KN_CYBER_ID = "n0000000-0000-0000-0000-000000000003"

# --- 基準日時 ---
_NOW = datetime(2025, 6, 15, 9, 0, 0, tzinfo=UTC)
_ONE_MONTH_AGO = _NOW - timedelta(days=30)
_TWO_WEEKS_AGO = _NOW - timedelta(days=14)
_ONE_WEEK_AGO = _NOW - timedelta(days=7)
_THREE_DAYS_AGO = _NOW - timedelta(days=3)

# デモユーザーの共通パスワード
DEMO_PASSWORD = "demo1234"


# --- トランスクリプト定義 ---

def _purchase_transcript() -> list[dict]:
    """購買プロセス内部統制ヒアリング トランスクリプト。"""
    entries = [
        {
            "speaker": "AI",
            "content": (
                "本日は購買プロセスの内部統制についてお伺いいたします。"
                "まず、御社の購買プロセスの全体的な流れを教えていただけますか？"
            ),
            "timestamp_ms": 0,
        },
        {
            "speaker": "INTERVIEWEE",
            "content": (
                "はい。当社の購買は基本的に、各部門からの購買申請、購買部門での発注処理、"
                "検収、そして経理部での支払い処理という流れになっています。"
                "システムとしてはSAPを使用しており、購買申請から支払いまで一連の流れが"
                "システム上で管理されています。"
            ),
            "timestamp_ms": 15000,
        },
        {
            "speaker": "AI",
            "content": (
                "ありがとうございます。購買申請の承認プロセスについて詳しく教えてください。"
                "承認権限はどのように設定されていますか？"
            ),
            "timestamp_ms": 45000,
        },
        {
            "speaker": "INTERVIEWEE",
            "content": (
                "承認は金額に応じた権限テーブルがあります。50万円未満は課長決裁、"
                "50万円以上500万円未満は部長決裁、500万円以上は取締役決裁となっています。"
                "また、ITシステム関連の購買については金額に関わらず情報システム部の"
                "事前承認が必要です。"
            ),
            "timestamp_ms": 70000,
        },
        {
            "speaker": "AI",
            "content": (
                "金額別の承認権限と、IT関連の特別ルールがあるのですね。"
                "では、発注先の選定プロセスについてお聞かせください。"
                "相見積もりの取得基準はどのようになっていますか？"
            ),
            "timestamp_ms": 105000,
        },
        {
            "speaker": "INTERVIEWEE",
            "content": (
                "100万円以上の案件では原則3社以上の相見積もりを取得します。"
                "100万円未満でも新規取引先の場合は2社以上必要です。"
                "ただし、保守契約の更新やソフトウェアライセンスなど"
                "合理的な理由がある場合は単独発注も認められますが、"
                "その場合は「単独発注理由書」を添付して部長承認を取得します。"
            ),
            "timestamp_ms": 130000,
        },
        {
            "speaker": "AI",
            "content": (
                "相見積もりの基準と例外処理が明確ですね。"
                "検収プロセスについてお伺いします。物品やサービスの検収はどのように行われていますか？"
            ),
            "timestamp_ms": 175000,
        },
        {
            "speaker": "INTERVIEWEE",
            "content": (
                "物品の場合は、発注担当者とは別の担当者が納品物を確認し、"
                "発注書と照合した上で検収処理を行います。いわゆる三者分離の原則ですね。"
                "サービスについては、成果物の確認を依頼部門が行い、"
                "検収書に署名をもらってからシステムに入力します。"
                "ただ、正直なところ、月末に集中するとチェックが形式的になることもあります。"
            ),
            "timestamp_ms": 200000,
        },
        {
            "speaker": "AI",
            "content": (
                "三者分離の原則を採用されているのですね。月末集中時の形式化は"
                "よくある課題です。支払い処理についてはいかがですか？"
                "支払い承認のプロセスを教えてください。"
            ),
            "timestamp_ms": 250000,
        },
        {
            "speaker": "INTERVIEWEE",
            "content": (
                "支払いは経理部で処理します。検収が完了した案件について、"
                "請求書と発注書・検収書の三点照合を行い、金額・数量の一致を確認します。"
                "支払い実行は経理課長の承認が必要で、500万円以上は経理部長の承認も必要です。"
                "振込データの作成と実行は別の担当者が行う分離統制になっています。"
            ),
            "timestamp_ms": 280000,
        },
        {
            "speaker": "AI",
            "content": (
                "三点照合と職務分離が整備されていますね。"
                "最後に、現状の購買プロセスで認識されている課題やリスクについて"
                "お聞かせいただけますか？"
            ),
            "timestamp_ms": 330000,
        },
        {
            "speaker": "INTERVIEWEE",
            "content": (
                "いくつかあります。まず、紙の見積書のPDF化が遅れることがあり、"
                "エビデンスの管理が追いついていない案件があります。"
                "また、子会社との取引について親会社と同じルールを適用しているのですが、"
                "実態として金額基準が子会社にはそぐわない部分があります。"
                "あと、SAPの権限設定について、異動時のIDの棚卸しが"
                "四半期ごとの実施にとどまっていて、タイムリーではないですね。"
            ),
            "timestamp_ms": 355000,
        },
        {
            "speaker": "AI",
            "content": (
                "貴重なご指摘ありがとうございます。エビデンス管理、子会社対応、"
                "アクセス権限管理の3点が主要な課題ということですね。"
                "本日のヒアリングは以上です。ご協力ありがとうございました。"
            ),
            "timestamp_ms": 410000,
        },
    ]
    return entries


def _sales_transcript() -> list[dict]:
    """売上プロセス内部統制ヒアリング トランスクリプト。"""
    entries = [
        {
            "speaker": "AI",
            "content": (
                "本日は売上プロセスの内部統制についてお伺いいたします。"
                "まず、御社の売上計上プロセスの概要を教えていただけますか？"
            ),
            "timestamp_ms": 0,
        },
        {
            "speaker": "INTERVIEWEE",
            "content": (
                "はい。当社はBtoB向けの金融サービスが主力で、売上は大きく分けると"
                "コンサルティングフィー、システム利用料、ライセンス収入の3種類です。"
                "コンサルティングは役務提供完了時、システム利用料は月額で毎月末に計上、"
                "ライセンスは契約期間に応じて按分計上しています。"
            ),
            "timestamp_ms": 15000,
        },
        {
            "speaker": "AI",
            "content": (
                "3種類の収益認識基準があるのですね。"
                "コンサルティングフィーの計上時期について、もう少し詳しく教えてください。"
                "「役務提供完了」はどのように判定されますか？"
            ),
            "timestamp_ms": 50000,
        },
        {
            "speaker": "INTERVIEWEE",
            "content": (
                "コンサルティングは成果物納品ベースです。クライアントに成果物を提出し、"
                "検収書を受領した時点で売上を計上します。長期プロジェクトの場合は"
                "マイルストーンごとに中間検収を設定し、段階的に売上を認識しています。"
                "期末に検収未了の案件は翌期回しとなります。"
            ),
            "timestamp_ms": 75000,
        },
        {
            "speaker": "AI",
            "content": (
                "検収書ベースで明確ですね。売上の承認・確認プロセスについて教えてください。"
                "誰がどの段階で確認していますか？"
            ),
            "timestamp_ms": 115000,
        },
        {
            "speaker": "INTERVIEWEE",
            "content": (
                "営業担当が案件情報と請求データを入力し、営業課長が一次承認します。"
                "その後、管理部門がクライアントとの契約書と請求内容の整合性を確認し、"
                "最終的に経理部が仕訳を計上します。月次で営業部と経理部の合同レビュー会議を"
                "開催して、計上済み案件の妥当性を確認しています。"
            ),
            "timestamp_ms": 140000,
        },
        {
            "speaker": "AI",
            "content": "与信管理についてはどのように運用されていますか？",
            "timestamp_ms": 190000,
        },
        {
            "speaker": "INTERVIEWEE",
            "content": (
                "新規取引先は必ず与信審査を実施します。信用調査会社のレポートと"
                "直近3期の財務諸表を基に与信限度額を設定しています。"
                "既存取引先は年1回の定期見直しと、信用不安情報があった場合の"
                "臨時見直しを行っています。与信限度額を超える取引は"
                "取締役会の個別承認が必要です。"
            ),
            "timestamp_ms": 210000,
        },
        {
            "speaker": "AI",
            "content": (
                "与信管理が体系的に整備されていますね。"
                "売上プロセスで現在認識されている課題はありますか？"
            ),
            "timestamp_ms": 260000,
        },
        {
            "speaker": "INTERVIEWEE",
            "content": (
                "課題としては、期末に検収が集中する傾向があり、営業部門に"
                "「検収の前倒し」を依頼するプレッシャーが生じることがあります。"
                "また、ライセンス収入の按分計上について、契約途中での"
                "スコープ変更があった場合の処理ルールが曖昧な部分があります。"
                "これは今期中にルールを明確化する予定です。"
            ),
            "timestamp_ms": 285000,
        },
        {
            "speaker": "AI",
            "content": (
                "期末の検収集中とライセンス按分ルールの明確化が課題ですね。"
                "本日のヒアリングは以上です。ご協力ありがとうございました。"
            ),
            "timestamp_ms": 340000,
        },
    ]
    return entries


def _compliance_mgr_transcript() -> list[dict]:
    """コンプライアンス意識調査（管理職） トランスクリプト（匿名）。"""
    entries = [
        {
            "speaker": "AI",
            "content": (
                "本日はコンプライアンス意識に関する匿名アンケートにご協力ください。"
                "回答内容は統計的に処理され、個人が特定されることはありません。"
                "まず、現在のコンプライアンス研修の有効性についてどうお感じですか？"
            ),
            "timestamp_ms": 0,
        },
        {
            "speaker": "INTERVIEWEE",
            "content": (
                "正直なところ、年1回のeラーニングでは形式的になっていると思います。"
                "受講率は高いですが、内容を本当に理解しているかは疑問です。"
                "もっと実務に即した事例ベースの研修があると良いと思います。"
            ),
            "timestamp_ms": 20000,
        },
        {
            "speaker": "AI",
            "content": (
                "研修の実効性に課題を感じているのですね。"
                "ハラスメントや不正行為を目撃・認知した場合の通報制度について"
                "どのように認識されていますか？"
            ),
            "timestamp_ms": 55000,
        },
        {
            "speaker": "INTERVIEWEE",
            "content": (
                "内部通報窓口があることは知っていますが、実際に利用した人を"
                "知りません。匿名性が本当に担保されるのか不安に思っている"
                "社員は多いと思います。外部窓口の存在も周知が不十分です。"
            ),
            "timestamp_ms": 80000,
        },
        {
            "speaker": "AI",
            "content": (
                "通報制度の信頼性が課題ですね。"
                "部下に対してコンプライアンスの重要性をどのように伝えていますか？"
            ),
            "timestamp_ms": 115000,
        },
        {
            "speaker": "INTERVIEWEE",
            "content": (
                "月次のチームミーティングで全社通達を共有するようにしていますが、"
                "日常業務に追われて十分な時間を割けていないのが実情です。"
                "コンプライアンスの話題は「また同じ話か」という空気になりがちで、"
                "伝え方に工夫が必要だと感じています。"
            ),
            "timestamp_ms": 140000,
        },
        {
            "speaker": "AI",
            "content": (
                "伝え方の工夫が必要とのことですね。"
                "コンプライアンス上、最も懸念しているリスクは何ですか？"
            ),
            "timestamp_ms": 180000,
        },
        {
            "speaker": "INTERVIEWEE",
            "content": (
                "個人情報の取り扱いです。顧客データを含むExcelファイルが"
                "メールで共有されることがまだあり、暗号化も徹底されていません。"
                "在宅勤務の拡大でリスクが増大していると感じます。"
                "あと、取引先との会食・贈答に関するルールが曖昧で、"
                "部下から相談を受けることが多いです。"
            ),
            "timestamp_ms": 205000,
        },
        {
            "speaker": "AI",
            "content": (
                "個人情報管理と贈収賄リスクが主要な懸念事項ですね。"
                "ご協力ありがとうございました。"
            ),
            "timestamp_ms": 255000,
        },
    ]
    return entries


def _cyber_it_transcript() -> list[dict]:
    """サイバーセキュリティリスクアセスメント（IT部門） トランスクリプト。"""
    entries = [
        {
            "speaker": "AI",
            "content": (
                "本日はサイバーセキュリティリスクについてお伺いいたします。"
                "まず、御社の情報セキュリティ管理体制の概要を教えてください。"
            ),
            "timestamp_ms": 0,
        },
        {
            "speaker": "INTERVIEWEE",
            "content": (
                "情報システム部が全社のセキュリティ管理を統括しています。"
                "CISOは取締役CTOが兼務しており、情報セキュリティ委員会が"
                "四半期ごとに開催されます。ISMSの認証は取得済みで、"
                "年次の外部監査も受けています。"
            ),
            "timestamp_ms": 15000,
        },
        {
            "speaker": "AI",
            "content": (
                "体制が整備されていますね。"
                "現在のネットワークセキュリティ対策について教えてください。"
            ),
            "timestamp_ms": 55000,
        },
        {
            "speaker": "INTERVIEWEE",
            "content": (
                "ファイアウォールとIDS/IPSを導入しており、WAFも"
                "外部公開サービスに適用しています。エンドポイントはEDRを全端末に導入済みです。"
                "ゼロトラストネットワークへの移行を進めており、"
                "現在約60%の業務アプリケーションがID認証ベースのアクセスに移行しています。"
            ),
            "timestamp_ms": 75000,
        },
        {
            "speaker": "AI",
            "content": (
                "ゼロトラストへの移行が進行中なのですね。"
                "インシデント対応体制について教えてください。"
                "CSIRT等の体制はどのようになっていますか？"
            ),
            "timestamp_ms": 120000,
        },
        {
            "speaker": "INTERVIEWEE",
            "content": (
                "CSIRTを設置しており、情報システム部のメンバー5名で構成しています。"
                "インシデント対応手順書はあり、年1回の訓練も実施しています。"
                "ただ、ランサムウェア等の高度な攻撃を想定した訓練は"
                "まだ実施できていません。外部のセキュリティベンダーと"
                "インシデントレスポンスの契約を結んでいます。"
            ),
            "timestamp_ms": 145000,
        },
        {
            "speaker": "AI",
            "content": (
                "CSIRTと外部連携が整備されていますね。"
                "従業員のセキュリティ教育・啓発活動はどのように行っていますか？"
            ),
            "timestamp_ms": 195000,
        },
        {
            "speaker": "INTERVIEWEE",
            "content": (
                "全社員向けのセキュリティ研修を年2回実施しています。"
                "標的型メール訓練は四半期ごとに実施しており、開封率は"
                "当初の30%から現在は8%程度まで低下しました。"
                "ただ、特定の部門では依然として開封率が高く、"
                "部門別のフォローアップ研修を検討しています。"
            ),
            "timestamp_ms": 220000,
        },
        {
            "speaker": "AI",
            "content": (
                "標的型メール訓練の成果が出ていますね。"
                "クラウドサービスのセキュリティ管理についてはいかがですか？"
            ),
            "timestamp_ms": 265000,
        },
        {
            "speaker": "INTERVIEWEE",
            "content": (
                "AWS、Azure、Microsoft 365を利用しています。"
                "クラウドの設定監査は月次で実施しており、"
                "CASBも導入してシャドーITの検知を行っています。"
                "課題としては、SaaS利用の増加に管理が追いついていない面があります。"
                "特にAPI連携のセキュリティレビューが十分でないケースがあります。"
            ),
            "timestamp_ms": 290000,
        },
        {
            "speaker": "AI",
            "content": (
                "クラウドセキュリティの課題が明確ですね。"
                "最後に、今後最も優先すべきセキュリティ課題は何だとお考えですか？"
            ),
            "timestamp_ms": 340000,
        },
        {
            "speaker": "INTERVIEWEE",
            "content": (
                "3つあります。まず、サプライチェーンリスクへの対応です。"
                "委託先のセキュリティ評価が不十分なケースがあります。"
                "次に、AI・生成AIの業務利用に関するセキュリティポリシーの策定です。"
                "社員が個人的に利用しているケースがあり、情報漏洩リスクがあります。"
                "最後に、BCPの観点でのバックアップ・復旧体制の強化です。"
                "現在のRPOは24時間ですが、4時間以内にしたいと考えています。"
            ),
            "timestamp_ms": 365000,
        },
        {
            "speaker": "AI",
            "content": (
                "サプライチェーン、生成AI、BCP/DRの3点が優先課題ですね。"
                "大変参考になりました。本日のヒアリングは以上です。ご協力ありがとうございました。"
            ),
            "timestamp_ms": 420000,
        },
    ]
    return entries


# --- デモデータ一括定義 ---

DEMO_DATA = {
    # === 組織 ===
    "organization": {
        "id": ORG_ID,
        "name": "テクノファイナンス株式会社",
        "settings": {
            "industry": "金融サービス",
            "employee_count": 800,
            "fiscal_year_end": "03-31",
            "default_language": "ja",
        },
    },
    # === ユーザー ===
    "users": [
        {
            "id": USER_ADMIN_ID,
            "email": "admin@demo.example.com",
            "name": "田中 太郎",
            "role": "admin",
            "organization_id": ORG_ID,
            "auth_provider": "local",
            "mfa_enabled": False,
        },
        {
            "id": USER_MANAGER_ID,
            "email": "manager@demo.example.com",
            "name": "鈴木 花子",
            "role": "manager",
            "organization_id": ORG_ID,
            "auth_provider": "local",
            "mfa_enabled": False,
        },
        {
            "id": USER_INTERVIEWER_ID,
            "email": "interviewer@demo.example.com",
            "name": "佐藤 健一",
            "role": "interviewer",
            "organization_id": ORG_ID,
            "auth_provider": "local",
            "mfa_enabled": False,
        },
        {
            "id": USER_VIEWER_ID,
            "email": "viewer@demo.example.com",
            "name": "山田 美咲",
            "role": "viewer",
            "organization_id": ORG_ID,
            "auth_provider": "local",
            "mfa_enabled": False,
        },
    ],
    # === プロジェクト ===
    "projects": [
        {
            "id": PROJECT_JSOX_ID,
            "name": "2025年度 J-SOX内部統制評価",
            "description": (
                "金融商品取引法に基づく内部統制報告制度（J-SOX）対応として、"
                "主要業務プロセス（購買・売上・IT統制）の内部統制の"
                "整備・運用状況を評価する。"
            ),
            "client_name": "テクノファイナンス株式会社",
            "organization_id": ORG_ID,
            "created_by": USER_ADMIN_ID,
            "status": "active",
            "start_date": date(2025, 4, 1),
            "end_date": date(2025, 9, 30),
        },
        {
            "id": PROJECT_COMPLIANCE_ID,
            "name": "全社コンプライアンス意識調査 2025",
            "description": (
                "全社員を対象としたコンプライアンス意識調査。"
                "匿名方式で実施し、コンプライアンス研修の実効性、"
                "内部通報制度の認知度、リスク認識等を把握する。"
            ),
            "client_name": "テクノファイナンス株式会社",
            "organization_id": ORG_ID,
            "created_by": USER_MANAGER_ID,
            "status": "active",
            "start_date": date(2025, 5, 1),
            "end_date": date(2025, 7, 31),
        },
        {
            "id": PROJECT_CYBER_ID,
            "name": "サイバーセキュリティリスクアセスメント",
            "description": (
                "サイバーセキュリティに関するリスクアセスメントを実施し、"
                "現状のセキュリティ対策の十分性を評価する。"
                "IT部門および経営層へのヒアリングを通じて、"
                "優先的に対応すべきリスクを特定する。"
            ),
            "client_name": "テクノファイナンス株式会社",
            "organization_id": ORG_ID,
            "created_by": USER_ADMIN_ID,
            "status": "active",
            "start_date": date(2025, 5, 15),
            "end_date": date(2025, 8, 31),
        },
    ],
    # === テンプレート ===
    "templates": [
        {
            "id": TPL_CONTROL_EVAL_ID,
            "name": "内部統制評価ヒアリングテンプレート",
            "description": "J-SOX対応の内部統制整備・運用状況評価用質問セット",
            "use_case_type": "control_evaluation",
            "organization_id": ORG_ID,
            "created_by": USER_ADMIN_ID,
            "questions": [
                {
                    "order": 1,
                    "question": "対象プロセスの全体的な流れを教えてください。",
                    "follow_ups": [
                        "各ステップの承認者は誰ですか？",
                        "システム化されている部分はどこですか？",
                    ],
                    "required": True,
                    "category": "プロセス概要",
                },
                {
                    "order": 2,
                    "question": "承認プロセスと権限設定について教えてください。",
                    "follow_ups": [
                        "金額に応じた権限の違いはありますか？",
                        "例外的な承認ルートはありますか？",
                    ],
                    "required": True,
                    "category": "統制活動",
                },
                {
                    "order": 3,
                    "question": "職務分離はどのように実施されていますか？",
                    "follow_ups": [
                        "担当者間の牽制が効いていますか？",
                        "代行時のルールはどうなっていますか？",
                    ],
                    "required": True,
                    "category": "統制活動",
                },
                {
                    "order": 4,
                    "question": "モニタリング活動について教えてください。",
                    "follow_ups": [
                        "定期的な点検・レビューはありますか？",
                        "発見した不備はどう対処していますか？",
                    ],
                    "required": True,
                    "category": "モニタリング",
                },
                {
                    "order": 5,
                    "question": "現在認識されているリスクや課題はありますか？",
                    "follow_ups": [
                        "改善に向けた取り組みは何かありますか？",
                        "経営層への報告体制はどうなっていますか？",
                    ],
                    "required": False,
                    "category": "リスク評価",
                },
            ],
            "settings": {"max_duration_minutes": 60, "language": "ja"},
            "version": 1,
            "is_published": True,
        },
        {
            "id": TPL_PROCESS_REVIEW_ID,
            "name": "業務プロセスレビューテンプレート",
            "description": "業務プロセスの効率性・有効性を評価するための質問セット",
            "use_case_type": "process_review",
            "organization_id": ORG_ID,
            "created_by": USER_ADMIN_ID,
            "questions": [
                {
                    "order": 1,
                    "question": "対象業務の目的と主要なKPIを教えてください。",
                    "follow_ups": ["KPIの達成状況はいかがですか？"],
                    "required": True,
                    "category": "概要",
                },
                {
                    "order": 2,
                    "question": "業務フローの中でボトルネックとなっている箇所はありますか？",
                    "follow_ups": ["改善の取り組みは進んでいますか？"],
                    "required": True,
                    "category": "効率性",
                },
                {
                    "order": 3,
                    "question": "ITツールの活用状況について教えてください。",
                    "follow_ups": ["手作業が残っている部分はありますか？"],
                    "required": False,
                    "category": "IT活用",
                },
            ],
            "settings": {"max_duration_minutes": 45, "language": "ja"},
            "version": 1,
            "is_published": True,
        },
        {
            "id": TPL_COMPLIANCE_ID,
            "name": "コンプライアンス意識調査テンプレート",
            "description": "全社コンプライアンス意識の匿名調査用質問セット",
            "use_case_type": "compliance_survey",
            "organization_id": ORG_ID,
            "created_by": USER_MANAGER_ID,
            "questions": [
                {
                    "order": 1,
                    "question": "コンプライアンス研修の有効性についてどう感じますか？",
                    "follow_ups": ["どのような改善を望みますか？"],
                    "required": True,
                    "category": "研修・教育",
                },
                {
                    "order": 2,
                    "question": "内部通報制度の認知度と信頼性についてどう思いますか？",
                    "follow_ups": ["制度の改善点はありますか？"],
                    "required": True,
                    "category": "通報制度",
                },
                {
                    "order": 3,
                    "question": "コンプライアンス上最も懸念しているリスクは何ですか？",
                    "follow_ups": ["具体的な事例があれば教えてください。"],
                    "required": True,
                    "category": "リスク認識",
                },
            ],
            "settings": {
                "max_duration_minutes": 30,
                "language": "ja",
                "anonymous_mode": True,
            },
            "version": 1,
            "is_published": True,
        },
        {
            "id": TPL_CYBER_RISK_ID,
            "name": "サイバーセキュリティリスク評価テンプレート",
            "description": "サイバーセキュリティ態勢の評価用質問セット",
            "use_case_type": "cyber_risk",
            "organization_id": ORG_ID,
            "created_by": USER_ADMIN_ID,
            "questions": [
                {
                    "order": 1,
                    "question": "情報セキュリティ管理体制の概要を教えてください。",
                    "follow_ups": [
                        "CISOの設置状況は？",
                        "セキュリティ委員会の運営状況は？",
                    ],
                    "required": True,
                    "category": "ガバナンス",
                },
                {
                    "order": 2,
                    "question": "ネットワークセキュリティ対策について教えてください。",
                    "follow_ups": [
                        "ゼロトラスト対応の進捗は？",
                        "エンドポイント対策の状況は？",
                    ],
                    "required": True,
                    "category": "技術対策",
                },
                {
                    "order": 3,
                    "question": "インシデント対応体制について教えてください。",
                    "follow_ups": [
                        "CSIRTの体制は？",
                        "訓練の実施頻度は？",
                    ],
                    "required": True,
                    "category": "インシデント対応",
                },
                {
                    "order": 4,
                    "question": "今後最も優先すべきセキュリティ課題は何ですか？",
                    "follow_ups": ["予算・人員の確保状況は？"],
                    "required": True,
                    "category": "優先課題",
                },
            ],
            "settings": {"max_duration_minutes": 60, "language": "ja"},
            "version": 1,
            "is_published": True,
        },
    ],
    # === タスク ===
    "tasks": [
        {
            "id": TASK_PURCHASE_ID,
            "name": "購買プロセス内部統制ヒアリング",
            "description": "購買プロセスの内部統制の整備・運用状況をヒアリングにより評価する。",
            "use_case_type": "control_evaluation",
            "project_id": PROJECT_JSOX_ID,
            "template_id": TPL_CONTROL_EVAL_ID,
            "created_by": USER_ADMIN_ID,
            "target_count": 1,
            "deadline": datetime(2025, 6, 30, tzinfo=UTC),
            "status": "completed",
            "settings": {},
        },
        {
            "id": TASK_SALES_ID,
            "name": "売上プロセス内部統制ヒアリング",
            "description": "売上計上プロセスの内部統制の整備・運用状況をヒアリングにより評価する。",
            "use_case_type": "process_review",
            "project_id": PROJECT_JSOX_ID,
            "template_id": TPL_PROCESS_REVIEW_ID,
            "created_by": USER_ADMIN_ID,
            "target_count": 1,
            "deadline": datetime(2025, 6, 30, tzinfo=UTC),
            "status": "completed",
            "settings": {},
        },
        {
            "id": TASK_IT_CONTROL_ID,
            "name": "IT全般統制評価ヒアリング",
            "description": "IT全般統制（アクセス管理、変更管理、運用管理等）の評価ヒアリング。",
            "use_case_type": "it_control",
            "project_id": PROJECT_JSOX_ID,
            "template_id": TPL_CONTROL_EVAL_ID,
            "created_by": USER_ADMIN_ID,
            "target_count": 1,
            "deadline": datetime(2025, 7, 31, tzinfo=UTC),
            "status": "in_progress",
            "settings": {},
        },
        {
            "id": TASK_COMP_MGR_ID,
            "name": "管理職向けコンプライアンス意識調査",
            "description": "管理職層を対象とした匿名コンプライアンス意識調査。",
            "use_case_type": "compliance_survey",
            "project_id": PROJECT_COMPLIANCE_ID,
            "template_id": TPL_COMPLIANCE_ID,
            "created_by": USER_MANAGER_ID,
            "target_count": 5,
            "deadline": datetime(2025, 6, 30, tzinfo=UTC),
            "status": "completed",
            "settings": {"anonymous_mode": True},
        },
        {
            "id": TASK_COMP_STAFF_ID,
            "name": "一般社員向けコンプライアンス意識調査",
            "description": "一般社員を対象とした匿名コンプライアンス意識調査。",
            "use_case_type": "compliance_survey",
            "project_id": PROJECT_COMPLIANCE_ID,
            "template_id": TPL_COMPLIANCE_ID,
            "created_by": USER_MANAGER_ID,
            "target_count": 10,
            "deadline": datetime(2025, 7, 15, tzinfo=UTC),
            "status": "in_progress",
            "settings": {"anonymous_mode": True},
        },
        {
            "id": TASK_CYBER_IT_ID,
            "name": "IT部門サイバーリスクヒアリング",
            "description": "情報システム部門へのサイバーセキュリティリスクアセスメントヒアリング。",
            "use_case_type": "cyber_risk",
            "project_id": PROJECT_CYBER_ID,
            "template_id": TPL_CYBER_RISK_ID,
            "created_by": USER_ADMIN_ID,
            "target_count": 1,
            "deadline": datetime(2025, 7, 31, tzinfo=UTC),
            "status": "completed",
            "settings": {},
        },
        {
            "id": TASK_CYBER_EXEC_ID,
            "name": "経営層サイバーリスクヒアリング",
            "description": "経営層へのサイバーセキュリティリスク認識・方針に関するヒアリング。",
            "use_case_type": "cyber_risk",
            "project_id": PROJECT_CYBER_ID,
            "template_id": TPL_CYBER_RISK_ID,
            "created_by": USER_ADMIN_ID,
            "target_count": 1,
            "deadline": datetime(2025, 8, 15, tzinfo=UTC),
            "status": "pending",
            "settings": {},
        },
    ],
    # === インタビュー対象者 ===
    "interviewees": [
        {
            "id": IEE_TAKAHASHI_ID,
            "organization_id": ORG_ID,
            "name": "高橋 誠",
            "email": "takahashi@technofinance.example.com",
            "department": "経理部",
            "position": "部長",
            "is_anonymous": False,
            "extra_metadata": {"years_in_role": 8},
        },
        {
            "id": IEE_WATANABE_ID,
            "organization_id": ORG_ID,
            "name": "渡辺 裕子",
            "email": "watanabe@technofinance.example.com",
            "department": "営業部",
            "position": "課長",
            "is_anonymous": False,
            "extra_metadata": {"years_in_role": 5},
        },
        {
            "id": IEE_ANON1_ID,
            "organization_id": ORG_ID,
            "name": None,
            "email": None,
            "department": None,
            "position": None,
            "is_anonymous": True,
            "extra_metadata": {"survey_group": "management"},
        },
        {
            "id": IEE_ANON2_ID,
            "organization_id": ORG_ID,
            "name": None,
            "email": None,
            "department": None,
            "position": None,
            "is_anonymous": True,
            "extra_metadata": {"survey_group": "management"},
        },
        {
            "id": IEE_KOBAYASHI_ID,
            "organization_id": ORG_ID,
            "name": "小林 大輔",
            "email": "kobayashi@technofinance.example.com",
            "department": "情報システム部",
            "position": "マネージャー",
            "is_anonymous": False,
            "extra_metadata": {"years_in_role": 6, "certifications": ["CISSP", "CISA"]},
        },
    ],
    # === インタビュー ===
    "interviews": [
        {
            "id": ITV_PURCHASE_ID,
            "task_id": TASK_PURCHASE_ID,
            "interviewee_id": IEE_TAKAHASHI_ID,
            "interviewer_id": USER_INTERVIEWER_ID,
            "language": "ja",
            "status": "completed",
            "started_at": _ONE_MONTH_AGO,
            "completed_at": _ONE_MONTH_AGO + timedelta(minutes=45),
            "duration_seconds": 2700,
            "summary": (
                "購買プロセスの内部統制は概ね整備されている。"
                "金額別承認権限テーブル、三者分離原則、三点照合が運用されている。"
                "課題として、エビデンスのPDF化遅延、子会社への金額基準の適合性、"
                "SAPアクセス権限の棚卸し頻度が挙げられた。"
            ),
            "ai_analysis": {
                "key_findings": [
                    "金額別承認権限テーブルが整備されている（50万/500万の閾値）",
                    "三者分離の原則を採用した検収プロセス",
                    "三点照合による支払い統制の実施",
                    "月末集中時の検収チェック形式化リスク",
                ],
                "risks_identified": [
                    {
                        "risk": "エビデンス管理の不備",
                        "severity": "medium",
                        "detail": "紙見積書のPDF化遅延によりエビデンス管理が不十分な案件が存在",
                    },
                    {
                        "risk": "子会社への金額基準不適合",
                        "severity": "medium",
                        "detail": "親会社と同一の金額基準が子会社の実態に合っていない",
                    },
                    {
                        "risk": "アクセス権限管理の遅延",
                        "severity": "high",
                        "detail": "SAPの権限棚卸しが四半期ごとにとどまり、異動時のタイムリーな反映ができていない",
                    },
                ],
                "control_effectiveness": "partially_effective",
                "recommendations": [
                    "エビデンスの電子化・自動保管の仕組み導入",
                    "子会社向け金額基準の見直し",
                    "SAPアクセス権限の月次棚卸し導入",
                ],
            },
            "extra_metadata": {"location": "本社会議室A", "recording": False},
            "transcript": _purchase_transcript(),
        },
        {
            "id": ITV_SALES_ID,
            "task_id": TASK_SALES_ID,
            "interviewee_id": IEE_WATANABE_ID,
            "interviewer_id": USER_INTERVIEWER_ID,
            "language": "ja",
            "status": "completed",
            "started_at": _TWO_WEEKS_AGO,
            "completed_at": _TWO_WEEKS_AGO + timedelta(minutes=40),
            "duration_seconds": 2400,
            "summary": (
                "売上プロセスは3種類の収益認識基準（コンサルティングフィー、"
                "システム利用料、ライセンス収入）で管理されている。"
                "検収書ベースの計上、月次レビュー会議等の統制が整備されている。"
                "課題として、期末の検収集中とライセンス按分ルールの曖昧さが指摘された。"
            ),
            "ai_analysis": {
                "key_findings": [
                    "3種類の収益認識基準が明確に区分されている",
                    "検収書ベースの売上計上による客観的な証拠",
                    "月次の営業・経理合同レビュー会議の実施",
                    "体系的な与信管理プロセスの整備",
                ],
                "risks_identified": [
                    {
                        "risk": "期末の検収集中",
                        "severity": "high",
                        "detail": "期末に検収が集中し、営業部門への前倒し圧力が生じるリスク",
                    },
                    {
                        "risk": "ライセンス按分ルールの曖昧さ",
                        "severity": "medium",
                        "detail": "契約途中のスコープ変更時の按分処理ルールが未整備",
                    },
                ],
                "control_effectiveness": "effective",
                "recommendations": [
                    "検収スケジュールの平準化施策の導入",
                    "ライセンス按分ルールの明文化と周知",
                ],
            },
            "extra_metadata": {"location": "本社会議室B", "recording": False},
            "transcript": _sales_transcript(),
        },
        {
            "id": ITV_IT_CONTROL_ID,
            "task_id": TASK_IT_CONTROL_ID,
            "interviewee_id": IEE_KOBAYASHI_ID,
            "interviewer_id": USER_INTERVIEWER_ID,
            "language": "ja",
            "status": "scheduled",
            "started_at": None,
            "completed_at": None,
            "duration_seconds": None,
            "summary": None,
            "ai_analysis": None,
            "extra_metadata": {
                "location": "本社会議室C",
                "scheduled_date": str(_NOW.date() + timedelta(days=3)),
            },
            "transcript": [],
        },
        {
            "id": ITV_COMP_MGR_ID,
            "task_id": TASK_COMP_MGR_ID,
            "interviewee_id": IEE_ANON1_ID,
            "interviewer_id": USER_INTERVIEWER_ID,
            "language": "ja",
            "status": "completed",
            "started_at": _ONE_WEEK_AGO,
            "completed_at": _ONE_WEEK_AGO + timedelta(minutes=25),
            "duration_seconds": 1500,
            "summary": (
                "コンプライアンス研修の形式化、内部通報制度の信頼性への懸念、"
                "個人情報管理と贈収賄リスクが主要な課題として挙げられた。"
                "管理職自身がコンプライアンス浸透に課題を感じている。"
            ),
            "ai_analysis": {
                "key_findings": [
                    "eラーニング研修の形式化（受講率は高いが理解度が不明）",
                    "内部通報制度の匿名性への不信感",
                    "コンプライアンス教育の伝え方に課題",
                    "個人情報管理のリスク（メール共有、暗号化不徹底）",
                ],
                "risks_identified": [
                    {
                        "risk": "通報制度への信頼欠如",
                        "severity": "high",
                        "detail": "匿名性が担保されるか不安視する社員が多い",
                    },
                    {
                        "risk": "個人情報漏洩リスク",
                        "severity": "high",
                        "detail": "顧客データを含むExcelファイルのメール共有が残存",
                    },
                    {
                        "risk": "贈収賄リスク",
                        "severity": "medium",
                        "detail": "取引先との会食・贈答ルールが曖昧",
                    },
                ],
                "survey_scores": {
                    "training_effectiveness": 2.8,
                    "reporting_trust": 2.3,
                    "risk_awareness": 3.5,
                    "management_commitment": 3.2,
                },
            },
            "extra_metadata": {"anonymous": True, "survey_group": "management"},
            "transcript": _compliance_mgr_transcript(),
        },
        {
            "id": ITV_CYBER_IT_ID,
            "task_id": TASK_CYBER_IT_ID,
            "interviewee_id": IEE_KOBAYASHI_ID,
            "interviewer_id": USER_INTERVIEWER_ID,
            "language": "ja",
            "status": "completed",
            "started_at": _THREE_DAYS_AGO,
            "completed_at": _THREE_DAYS_AGO + timedelta(minutes=50),
            "duration_seconds": 3000,
            "summary": (
                "セキュリティ管理体制はISMS認証取得済みで基盤は整備されている。"
                "ゼロトラスト移行は60%完了。CSIRTを設置し外部ベンダーとも連携。"
                "標的型メール訓練で開封率を30%→8%に改善。"
                "優先課題はサプライチェーンリスク、生成AIポリシー、BCP/DR強化の3点。"
            ),
            "ai_analysis": {
                "key_findings": [
                    "ISMS認証取得済み、年次外部監査を実施",
                    "ゼロトラストネットワーク移行60%完了",
                    "CSIRT設置、外部インシデントレスポンス契約あり",
                    "標的型メール訓練で開封率30%→8%に改善",
                    "CASB導入によるシャドーIT検知を実施",
                ],
                "risks_identified": [
                    {
                        "risk": "サプライチェーンリスク",
                        "severity": "high",
                        "detail": "委託先のセキュリティ評価が不十分",
                    },
                    {
                        "risk": "生成AI利用リスク",
                        "severity": "high",
                        "detail": "社員の個人的な生成AI利用による情報漏洩リスク",
                    },
                    {
                        "risk": "BCP/DR体制",
                        "severity": "medium",
                        "detail": "RPO24時間→目標4時間への改善が必要",
                    },
                    {
                        "risk": "SaaS管理の不十分さ",
                        "severity": "medium",
                        "detail": "SaaS増加に管理が追いつかず、API連携のレビュー不足",
                    },
                ],
                "maturity_level": "managed",
                "nist_csf_scores": {
                    "identify": 3.5,
                    "protect": 3.8,
                    "detect": 3.2,
                    "respond": 2.8,
                    "recover": 2.5,
                },
            },
            "extra_metadata": {"location": "本社会議室D", "recording": False},
            "transcript": _cyber_it_transcript(),
        },
    ],
    # === レポート ===
    "reports": [
        {
            "id": RPT_PURCHASE_PROC_ID,
            "interview_id": ITV_PURCHASE_ID,
            "task_id": TASK_PURCHASE_ID,
            "created_by": USER_INTERVIEWER_ID,
            "approved_by": USER_ADMIN_ID,
            "report_type": "process_doc",
            "title": "購買プロセス業務記述書",
            "content": {
                "process_name": "購買プロセス",
                "process_owner": "購買部 部長",
                "overview": (
                    "購買申請→承認→発注→検収→支払いの一連の購買プロセス。"
                    "SAPにより一元管理。"
                ),
                "steps": [
                    {
                        "step": 1,
                        "name": "購買申請",
                        "description": "各部門がSAPで購買申請を起票",
                        "controls": ["金額別承認権限テーブルによる承認"],
                    },
                    {
                        "step": 2,
                        "name": "発注処理",
                        "description": "購買部門が発注書を作成・送付",
                        "controls": ["100万以上は3社以上の相見積もり取得"],
                    },
                    {
                        "step": 3,
                        "name": "検収",
                        "description": "発注担当者とは別の担当者が納品物を確認",
                        "controls": ["三者分離の原則", "発注書との照合確認"],
                    },
                    {
                        "step": 4,
                        "name": "支払い",
                        "description": "経理部が請求書・発注書・検収書の三点照合後に支払い",
                        "controls": ["三点照合", "振込作成と実行の分離統制"],
                    },
                ],
                "key_controls_count": 6,
                "identified_gaps": 3,
            },
            "format": "json",
            "status": "approved",
            "approved_at": _TWO_WEEKS_AGO,
        },
        {
            "id": RPT_PURCHASE_RCM_ID,
            "interview_id": ITV_PURCHASE_ID,
            "task_id": TASK_PURCHASE_ID,
            "created_by": USER_INTERVIEWER_ID,
            "approved_by": None,
            "report_type": "rcm",
            "title": "購買プロセス リスクコントロールマトリクス",
            "content": {
                "process_name": "購買プロセス",
                "items": [
                    {
                        "risk_id": "R-PUR-001",
                        "risk_description": "不正な購買申請が承認される",
                        "risk_category": "承認統制",
                        "control_id": "C-PUR-001",
                        "control_description": "金額別承認権限テーブルに基づく多段階承認",
                        "control_type": "preventive",
                        "frequency": "per_transaction",
                        "effectiveness": "effective",
                    },
                    {
                        "risk_id": "R-PUR-002",
                        "risk_description": "不適正な取引先への発注",
                        "risk_category": "取引先管理",
                        "control_id": "C-PUR-002",
                        "control_description": "100万以上は3社以上の相見積もり取得義務",
                        "control_type": "preventive",
                        "frequency": "per_transaction",
                        "effectiveness": "effective",
                    },
                    {
                        "risk_id": "R-PUR-003",
                        "risk_description": "架空検収による不正支払い",
                        "risk_category": "検収統制",
                        "control_id": "C-PUR-003",
                        "control_description": "発注者・検収者・支払承認者の三者分離",
                        "control_type": "preventive",
                        "frequency": "per_transaction",
                        "effectiveness": "partially_effective",
                        "gap_description": "月末集中時にチェックが形式化する場合あり",
                    },
                    {
                        "risk_id": "R-PUR-004",
                        "risk_description": "不正な支払いの実行",
                        "risk_category": "支払統制",
                        "control_id": "C-PUR-004",
                        "control_description": "請求書・発注書・検収書の三点照合",
                        "control_type": "detective",
                        "frequency": "per_transaction",
                        "effectiveness": "effective",
                    },
                ],
                "total_risks": 4,
                "total_controls": 4,
                "effective_controls": 3,
                "gaps_requiring_remediation": 1,
            },
            "format": "json",
            "status": "review",
            "approved_at": None,
        },
        {
            "id": RPT_SALES_WP_ID,
            "interview_id": ITV_SALES_ID,
            "task_id": TASK_SALES_ID,
            "created_by": USER_INTERVIEWER_ID,
            "approved_by": None,
            "report_type": "audit_workpaper",
            "title": "売上プロセス内部統制 監査調書",
            "content": {
                "workpaper_ref": "WP-SALES-2025-001",
                "audit_objective": "売上プロセスの内部統制の整備・運用状況を評価する",
                "scope": "コンサルティングフィー、システム利用料、ライセンス収入の計上プロセス",
                "procedures_performed": [
                    "売上計上プロセスの担当者へのヒアリング実施",
                    "承認プロセスの文書確認",
                    "与信管理プロセスの確認",
                ],
                "findings": [
                    {
                        "finding_id": "F-SALES-001",
                        "title": "期末の検収集中リスク",
                        "severity": "significant",
                        "description": "期末に検収が集中し、営業部門への前倒し圧力が生じるリスク",
                        "recommendation": "検収スケジュールの平準化施策の導入",
                    },
                    {
                        "finding_id": "F-SALES-002",
                        "title": "ライセンス按分ルールの未整備",
                        "severity": "moderate",
                        "description": "契約途中のスコープ変更時の按分処理ルールが未整備",
                        "recommendation": "ルールの明文化と社内周知",
                    },
                ],
                "conclusion": (
                    "売上プロセスの内部統制は全体として有効に機能しているが、"
                    "期末の検収集中リスクとライセンス按分ルールの整備が必要。"
                ),
                "prepared_by": "佐藤 健一",
                "reviewed_by": None,
            },
            "format": "json",
            "status": "draft",
            "approved_at": None,
        },
        {
            "id": RPT_COMP_SURVEY_ID,
            "interview_id": ITV_COMP_MGR_ID,
            "task_id": TASK_COMP_MGR_ID,
            "created_by": USER_MANAGER_ID,
            "approved_by": None,
            "report_type": "survey_analysis",
            "title": "管理職コンプライアンス意識調査 分析レポート",
            "content": {
                "survey_title": "全社コンプライアンス意識調査 2025（管理職）",
                "respondent_count": 1,
                "target_group": "management",
                "summary": (
                    "コンプライアンス研修の形式化と内部通報制度の信頼性が主要課題。"
                    "個人情報管理と贈収賄リスクに対する懸念が高い。"
                ),
                "key_metrics": {
                    "training_effectiveness": {"score": 2.8, "max": 5.0, "trend": "flat"},
                    "reporting_trust": {"score": 2.3, "max": 5.0, "trend": "declining"},
                    "risk_awareness": {"score": 3.5, "max": 5.0, "trend": "improving"},
                    "management_commitment": {"score": 3.2, "max": 5.0, "trend": "flat"},
                },
                "recommendations": [
                    "事例ベースのコンプライアンス研修の導入",
                    "外部通報窓口の周知強化",
                    "個人情報取り扱いルールの再徹底",
                    "贈収賄ポリシーの明確化と FAQ 整備",
                ],
            },
            "format": "json",
            "status": "review",
            "approved_at": None,
        },
        {
            "id": RPT_CYBER_SUMMARY_ID,
            "interview_id": ITV_CYBER_IT_ID,
            "task_id": TASK_CYBER_IT_ID,
            "created_by": USER_ADMIN_ID,
            "approved_by": None,
            "report_type": "summary",
            "title": "サイバーセキュリティリスクアセスメント サマリレポート",
            "content": {
                "assessment_scope": "全社サイバーセキュリティ態勢",
                "overall_maturity": "managed",
                "nist_csf_scores": {
                    "identify": 3.5,
                    "protect": 3.8,
                    "detect": 3.2,
                    "respond": 2.8,
                    "recover": 2.5,
                },
                "strengths": [
                    "ISMS認証取得・年次外部監査の実施",
                    "ゼロトラスト移行の推進（60%完了）",
                    "標的型メール訓練による啓発効果",
                ],
                "priority_actions": [
                    {
                        "priority": 1,
                        "action": "サプライチェーンセキュリティ評価の強化",
                        "timeline": "3ヶ月以内",
                    },
                    {
                        "priority": 2,
                        "action": "生成AI利用ポリシーの策定と周知",
                        "timeline": "1ヶ月以内",
                    },
                    {
                        "priority": 3,
                        "action": "BCP/DR計画の見直し（RPO目標4時間）",
                        "timeline": "6ヶ月以内",
                    },
                ],
            },
            "format": "json",
            "status": "draft",
            "approved_at": None,
        },
    ],
    # === ナレッジ ===
    "knowledge_items": [
        {
            "id": KN_PURCHASE_ID,
            "organization_id": ORG_ID,
            "source_interview_id": ITV_PURCHASE_ID,
            "title": "購買プロセスの承認権限テーブル設計",
            "content": (
                "金額に応じた多段階承認制度の設計事例。50万円未満は課長決裁、"
                "50万～500万円は部長決裁、500万円以上は取締役決裁。"
                "ITシステム関連は金額に関わらず情報システム部の事前承認を必要とする"
                "クロスファンクショナルな統制の例。"
            ),
            "source_type": "interview",
            "tags": ["購買", "承認権限", "内部統制", "J-SOX"],
            "extra_metadata": {"use_case": "control_evaluation"},
        },
        {
            "id": KN_SALES_ID,
            "organization_id": ORG_ID,
            "source_interview_id": ITV_SALES_ID,
            "title": "複合収益モデルの収益認識基準",
            "content": (
                "BtoB金融サービス企業における3種類の収益認識基準の適用事例。"
                "コンサルティング（検収書ベース）、システム利用料（月額計上）、"
                "ライセンス（按分計上）の区分管理。マイルストーン検収による"
                "長期プロジェクトの段階的売上認識の実践例。"
            ),
            "source_type": "interview",
            "tags": ["売上", "収益認識", "J-SOX", "金融サービス"],
            "extra_metadata": {"use_case": "process_review"},
        },
        {
            "id": KN_CYBER_ID,
            "organization_id": ORG_ID,
            "source_interview_id": ITV_CYBER_IT_ID,
            "title": "ゼロトラストネットワーク移行の実践事例",
            "content": (
                "中堅金融サービス企業におけるゼロトラストネットワーク移行の進捗事例。"
                "EDR全端末導入、CASB導入によるシャドーIT検知、"
                "ID認証ベースアクセスへの段階的移行（60%完了時点）。"
                "課題としてSaaS管理の複雑化とAPI連携セキュリティレビューの必要性が判明。"
            ),
            "source_type": "interview",
            "tags": ["サイバーセキュリティ", "ゼロトラスト", "CASB", "EDR"],
            "extra_metadata": {"use_case": "cyber_risk"},
        },
    ],
}
