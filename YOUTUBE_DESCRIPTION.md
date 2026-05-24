# YouTube 概要欄テキスト

動画完成後、以下をそのまま YouTube の概要欄に貼り付けてください。
（`【動画タイトル】` などは適宜書き換え）

---

AIで生成した楽曲のボーカルを入れ替え、複数の歌声をセクションごとに割り当てて1曲に再構成しました。

▼ 制作に使ったコード（GitHub）
https://github.com/Tatsuki-Choki/ai-idol-vocal-remix
※ 割り当ては arrangement.json の編集だけで完結する、データ駆動の音声/動画編集プロジェクトです。

━━━━━━━━━━━━━━━
🎬 制作ワークフロー
━━━━━━━━━━━━━━━

① 楽曲を生成（Suno）
　AI音楽生成「Suno」で楽曲を作成し、ダウンロード。
　https://suno.com/

② Controlla Voice にアップロード
　生成した楽曲を「Controlla Voice」にアップロード。
　https://voice.controlla.xyz/?ref=gibkun1

③ Swap Voice で声を入れ替え
　「Swap Voice」機能に、登録した声の情報を与えて実行。
　すると次の3つのデータが出力されます：
　　・元楽曲の BGM（インスト）のみ
　　・元楽曲のボーカルを分離したデータ
　　・新しくクリエイトした歌声の音声データ

④ Claude Code でミックス
　出力された各トラックをダウンロードし、Claude Code 上でミックス。
　BGM の上に複数の歌声をセクション単位（Aメロ／Bメロ／サビ）で
　割り当て、1曲に再構成しています。
　（Aメロ＝オリジナル / Bメロ＝クリエイト / サビ＝ユニゾン）

━━━━━━━━━━━━━━━

#AI音楽 #Suno #ControllaVoice #ClaudeCode #ボイスチェンジ
