import streamlit as st
import google.generativeai as genai
import os
import PIL.Image

# ページ設定
st.set_page_config(page_title="ママのためのAI数学解説", page_icon="📝")

# --- CSS ---
st.markdown("""
<style>
    .ad-banner {
        background-color: #f0f8ff;
        padding: 15px;
        border-radius: 10px;
        border: 2px dashed #4169e1;
        text-align: center;
        margin-bottom: 20px;
    }
    .main-header {
        text-align: center;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

# --- 関数: 確実に動くモデルを見つける ---
def get_working_model():
    """APIキーを使って実際に通信できるモデルを探し出します"""
    try:
        # 1. 利用可能なモデル一覧を取得
        models = list(genai.list_models())
        
        # 2. 'generateContent' が使えるモデルの名前リストを作る
        vision_models = []
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                vision_models.append(m.name)
        
        # 3. 優先順位に従ってモデルを選ぶ（リストにある正確な名前を使う）
        # Flash -> Pro Vision -> Pro の順で探す
        for target in ['flash', 'vision', 'pro']:
            for name in vision_models:
                if target in name:
                    return genai.GenerativeModel(name)
        
        # 見つからなければ最初のものを返す
        if vision_models:
            return genai.GenerativeModel(vision_models[0])
            
        return None
    except Exception as e:
        st.error(f"モデルリストの取得に失敗しました: {e}")
        return None

# --- 関数: 解説生成 ---
def generate_explanation(image, user_text):
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "エラー: APIキーが設定されていません。"
    
    genai.configure(api_key=api_key)
    
    # ★自動検出したモデルを使用
    model = get_working_model()
    if not model:
        return "エラー: 利用可能なAIモデルが見つかりませんでした。"

    # プロンプト作成
    base_prompt = """
    あなたは中学生・高校生に数学を教える優しい先生です。
    ユーザーから提供された「画像」と「補足テキスト」をもとに問題を解き、以下のフォーマットで解説してください。
    
    1. 【答え】: 最初に答えをズバリ書く
    2. 【考え方】: どう解くかの方針
    3. 【解説】: 式変形を含めて丁寧に。数式はLaTeX形式 ($...$) で書いてください。
    """
    
    # 画像とテキストをリストにまとめる
    input_content = [base_prompt]
    if user_text:
        input_content.append(f"【ユーザーからの補足情報】: {user_text}")
    input_content.append(image)
    
    try:
        # 生成実行
        response = model.generate_content(input_content)
        return response.text
    except Exception as e:
        return f"エラーが発生しました。\n使用モデル: {model.model_name}\n詳細: {e}"

# ==========================================
# アプリ画面
# ==========================================

# ヘッダー
st.markdown("<h1 class='main-header'>📝 ママのためのAI数学解説</h1>", unsafe_allow_html=True)
st.caption("写真を撮るだけ。AIが個別指導塾のような解説を作ります。")

# --- 【広告エリア A】 ---
st.markdown("""
<div class='ad-banner'>
    <h3>📢 【PR】お子様の成績にお悩みですか？</h3>
    <p>当社のオンライン学習サービスなら、月額〇〇円で質問し放題！</p>
    <a href="https://your-service-url.com" target="_blank">👉 詳しくはこちら（無料体験あり）</a>
</div>
""", unsafe_allow_html=True)

# 入力エリア
st.subheader("1. 問題を入力する")
uploaded_file = st.file_uploader("問題の写真をアップロードしてください", type=["jpg", "png", "jpeg"])
user_note = st.text_area("補足情報（任意）", placeholder="（例）問3だけ教えてください...", height=100)

if uploaded_file:
    # 画像を表示
    st.image(uploaded_file, caption='アップロードされた問題', use_column_width=True)
    
    if st.button('解説を作成する'):
        with st.spinner('AI先生が解説を書いています... ✏️'):
            try:
                # ★画像を安全な形式（RGB）に変換して読み込む
                image = PIL.Image.open(uploaded_file).convert('RGB')
                
                # 解説生成
                explanation = generate_explanation(image, user_note)
                
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
                # --- 【広告エリア B】 ---
                st.markdown("""
                <div class='ad-banner' style='background-color: #fff0f5; border-color: #ff69b4;'>
                    <h3>🎉 PDFが届くまでの間に...</h3>
                    <p><strong>「解き直し」こそが成績アップの鍵です。</strong></p>
                    <a href="https://your-service-url.com" target="_blank" style='font-size: 1.2em; font-weight: bold;'>👉 今だけ初月無料キャンペーン中！</a>
                </div>
                """, unsafe_allow_html=True)
            elif submitted:
                st.error("正しいメールアドレスを入力してください。")
