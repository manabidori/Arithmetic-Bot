import streamlit as st
import google.generativeai as genai
import os
import PIL.Image

# ページ設定
st.set_page_config(page_title="ママのためのAI数学解説", page_icon="📝")

# --- CSS（デザイン調整） ---
st.markdown("""
<style>
    /* 広告バナーのデザイン */
    .ad-banner {
        background-color: #f0f8ff;
        padding: 15px;
        border-radius: 10px;
        border: 2px dashed #4169e1;
        text-align: center;
        margin-bottom: 20px;
        color: #333333; /* 文字色を黒に固定 */
    }
    .ad-banner h3 {
        color: #333333 !important;
    }
    .ad-banner p {
        color: #333333 !important;
    }
    
    .main-header {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- 関数: 確実に動くモデルを見つける ---
def get_working_model():
    try:
        models = list(genai.list_models())
        vision_models = []
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                vision_models.append(m.name)
        
        for target in ['flash', 'vision', 'pro']:
            for name in vision_models:
                if target in name:
                    return genai.GenerativeModel(name)
        
        if vision_models:
            return genai.GenerativeModel(vision_models[0])
            
        return None
    except Exception as e:
        st.error(f"モデルリストの取得に失敗しました: {e}")
        return None

# --- 関数: 解説生成 ---
def generate_explanation(image, user_text, grade_level):
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "エラー: APIキーが設定されていません。"
    
    genai.configure(api_key=api_key)
    
    model = get_working_model()
    if not model:
        return "エラー: 利用可能なAIモデルが見つかりませんでした。"

    base_prompt = f"""
    あなたはプロの家庭教師です。
    ユーザーから提供された「画像」の問題を解き、以下の条件に従って解説してください。
    
    【対象者】
    この解説を読むのは **{grade_level}** の子供とその保護者です。
    
    【制約事項】
    1. **未習範囲の禁止**: {grade_level}までに習わない公式や知識は絶対に使わないでください。
    2. **わかりやすさ**: 専門用語は避け、子供が一人でも読めるように噛み砕いて説明してください。
    
    【出力フォーマット】
    ## 1. 答え
    （答えをズバリ書く）
    
    ## 2. 考え方
    （この問題を解くためのポイントや方針を短く）
    
    ## 3. 詳しい解説
    （式変形を含めて丁寧に。数式はLaTeX形式 $...$ で書く）
    
    ## 4. 別の解き方（もしあれば）
    （別解や、検算の方法、図を使った考え方など）
    """
    
    input_content = [base_prompt]
    if user_text:
        input_content.append(f"【ユーザーからの補足情報】: {user_text}")
    input_content.append(image)
    
    try:
        response = model.generate_content(input_content)
        return response.text
    except Exception as e:
        return f"エラーが発生しました。\n使用モデル: {model.model_name}\n詳細: {e}"

# ==========================================
# アプリ画面
# ==========================================

# ヘッダー
st.markdown("<h1 class='main-header'>📝 ママのためのAI数学解説</h1>", unsafe_allow_html=True)
st.caption("写真を撮るだけ。AIがお子様の学年に合わせた解説を作ります。")

# 広告A
st.markdown("""
<div class='ad-banner'>
    <h3>📢 【PR】お子様の成績にお悩みですか？</h3>
    <p>当社のオンライン学習サービスなら、月額〇〇円で質問し放題！</p>
    <a href="https://your-service-url.com" target="_blank">👉 詳しくはこちら（無料体験あり）</a>
</div>
""", unsafe_allow_html=True)

# 入力エリア
st.subheader("1. 問題を入力する")

grade_options = [
    "小学1年生", "小学2年生", "小学3年生", "小学4年生", "小学5年生", "小学6年生",
    "中学1年生", "中学2年生", "中学3年生", "高校生以上"
]
selected_grade = st.selectbox("お子様の学年を選んでください", grade_options, index=2)

uploaded_file = st.file_uploader("問題の写真をアップロードしてください", type=["jpg", "png", "jpeg"])
user_note = st.text_area("補足情報（任意）", placeholder="（例）問3だけ教えてください...", height=100)

if uploaded_file:
    st.image(uploaded_file, caption='アップロードされた問題', use_column_width=True)
    
    if st.button('解説を作成する'):
        with st.spinner(f'{selected_grade}向けの解説を作成しています... ✏️'):
            try:
                image = PIL.Image.open(uploaded_file).convert('RGB')
                explanation = generate_explanation(image, user_note, selected_grade)
                st.session_state['explanation'] = explanation
                st.session_state['show_email_form'] = True
            except Exception as e:
                st.error(f"画像の読み込み処理でエラーが発生しました: {e}")

# 解説 & オファーエリア
if 'explanation' in st.session_state:
    st.markdown("---")
    st.subheader("💡 AIによる解説")
    st.write(st.session_state['explanation'])
    st.markdown("---")

    if st.session_state.get('show_email_form'):
        st.info("💡 **この解説を「お子様用プリント（PDF）」にして受け取りますか？**")
        st.write("メールアドレスを入力すると、整ったレイアウトのPDF版解説をお送りします。")
        
        with st.form("email_form"):
            user_email = st.text_input("メールアドレスを入力", placeholder="example@email.com")
            submitted = st.form_submit_button("PDFをメールで受け取る 📩")
            
            if submitted and user_email and "@" in user_email:
                st.success("ありがとうございます！ 送信を受け付けました。")
                st.balloons()
                # 広告B
                st.markdown("""
                <div class='ad-banner' style='background-color: #fff0f5; border-color: #ff69b4;'>
                    <h3>🎉 PDFが届くまでの間に...</h3>
                    <p><strong>「解き直し」こそが成績アップの鍵です。</strong></p>
                    <a href="https://your-service-url.com" target="_blank" style='font-size: 1.2em; font-weight: bold;'>👉 今だけ初月無料キャンペーン中！</a>
                </div>
                """, unsafe_allow_html=True)
            elif submitted:
                st.error("正しいメールアドレスを入力してください。")
