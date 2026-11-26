---
lab:
  title: Microsoft Foundry で情報抽出をはじめよう​
  description: AI モデルを使用して視覚データから情報を抽出します。
  level: 200
  duration: 25 minutes
  islab: true
  primarytopics:
    - Microsoft Foundry
---

# Microsoft Foundry で情報抽出をはじめよう

この演習では、Microsoft のインテリジェント アプリケーション作成プラットフォームである Foundry の Azure Content Understanding を使用します。

Azure Content Understanding は AI モデルを使用して、構造化されていないマルチモーダル コンテンツ（ドキュメント、画像、動画、音声）を JSON などの構造化された使用可能な出力に変換する Foundry サービスです。信頼スコアとソースのグラウンディングを用いて、フィールドの抽出、分類、生成によってコンテンツを処理します。

この演習の所要時間は約 **20** 分です。

>**注**: この演習では *新しい* Foundry ポータル エクスペリエンスを使用します。

> **前提条件**: 演習環境準備 (00) で作成した Microsoft Foundry プロジェクトを使用します。まだプロジェクトを作成していない場合は、先に 00 の演習を完了してください。

## 新しい Foundry ポータルでドキュメントから情報を抽出する

1. Web ブラウザーで `https://ai.azure.com` の <a href="https://ai.azure.com" target="_blank">Microsoft Foundry</a> を開き、Azure の資格情報を使用してサインインします。演習環境準備 (00) で作成したプロジェクトを選択します。

2. *新しい* Foundry ポータルで、画面上部のメニューから **ビルド** を選択します。
3. 画面左側のメニューから **サービス** を選択します。

4. 一覧から **Document Intelligence and Content Understanding** のタイルを選択します。

5. 一覧から **> Content extraction** の項目を展開し、 **OCR (Read)** を選択します。

#### Content Understanding の *Read* 機能を試す

*Read* 機能はコンテンツ理解の最初のステップで、テキストを読んで抽出しますが、まだ構造や意味の理解は試みません。

1. **Category** ドロップダウンから **Content extraction** 、 **Prebuilt** ドロップダウンから **OCR (Read)** が選択されていることを確認します。

2. サンプルの **read_barcode.pdf** を選択し、**▶Run** ボタンを使用してドキュメントから情報を抽出します。分析が完了したら結果を確認します。

    ![サンプル請求書の分析結果のスクリーンショット。](./media/content-understanding-read.JPG)

3. 次の機能を試すには、ドロップダウンから別のアナライザーを選択します。

#### Content Understanding の *Layout* 機能を試す

1. **Category** ドロップダウンは **Content extraction** のまま、 **Prebuilt** ドロップダウンを **レイアウト** に変更します。

2. サンプルの **layout_checklist.jpg** を選択し、**▶Run** ボタンを使用して情報を抽出します。分析が完了したら結果を確認します。

    ![レイアウト チェックリストの分析結果のスクリーンショット。](./media/content-understanding-layout.JPG)

3. コンテンツ出力で **テーブル** タブを選択します。*レイアウト* アナライザーがコンテンツのテキストと構造の両方を取得できることを確認します。

    ![レイアウト チェックリスト分析のテーブル結果のスクリーンショット。](./media/content-understanding-layout-table.png)

4. 次の機能を試すには、ドロップダウンから別のアナライザーを選択します。

#### Content Understanding のその他のアナライザー機能を試す

1. **Category** ドロップダウンから **General document extraction** を選択します。**Prebuilt** のドロップダウンが **ドキュメントのフィールド** となっていることを確認します。

2. **モデル デプロイが必要(Model setup needed.)** ダイアログが表示された場合は、ダイアログ右端の **Set model defaults（デフォルトモデルのデプロイ）** を選択します。

3. 右側の **Default model deployments** パネルが開きます。**ドキュメントのフィールド アナライザー** には追加のモデル デプロイが必要です。**チャット補完モデル** と **チャット補完モデル(mini)** 、 **埋め込みモデル** のドロップダウンから推奨モデルを選択します。次に **変更の適用** を選択します。

    ![構成パネルでモデルを選択するスクリーンショット。](./media/content-understanding-model-config.PNG)

    >**ヒント**: *ドキュメントのフィールド* やその他の複雑な抽出ニーズには、複数の AI モデルのデプロイが必要です。各デプロイは特定のモデル バージョンまたは機能に紐付けられているためです。Azure AI Foundry で複数のモデルを使用することで、さまざまな種類の処理タスクをより効果的に処理でき、各ニーズに適切なモデルを選択する柔軟性が得られます。

4. 選択（デプロイ）が完了したら **Save defaults** をクリックして設定を保存します。

5. フル アナライザーを独自の請求書で試してみましょう。リポジトリ内の `data/06a-content-understanding/contoso-invoice-1.zip` から **<a href="https://raw.githubusercontent.com/ctct-edu/AI-901-Lab/main/data/06a-content-understanding/contoso-invoice-1.zip" target="_blank">contoso-invoice-1.zip</a>** をダウンロードして展開し、**contoso-invoice-1.pdf** を使用します。

6. **ファイルの参照** リンクを使用して、ダウンロードした **contoso-invoice-1.pdf** ドキュメントをアップロードします。**▶Run** を選択して結果を確認します。テキストがレンダリングされるだけでなく、レイアウトが取得され、フィールドが体系的なカテゴリに整理されていることに注目してください。

7. 抽出されたフィールドが表示されている右側のペインで、**結果** タブを選択して JSON の生の結果を表示します。使用されたアナライザーの種類が含まれている **analyzerID** フィールドを確認します。組み込みの Content Understanding アナライザーのリストは[こちら](https://learn.microsoft.com/azure/ai-services/content-understanding/concepts/prebuilt-analyzers)で確認できます。

     ![Document アナライザーを使用した請求書分析の JSON 結果のスクリーンショット。](./media/content-understanding-layout-json.png)

>**ヒント**: *フィールド* タブは *結果* タブの生の JSON からの情報をユーザーにわかりやすい形で表示していることを覚えておいてください。

## まとめ

この演習では、Foundry の Azure Content Understanding を探索し、非構造化コンテンツを構造化された使用可能なデータに変換する方法を学びました。3 つのアナライザーを試し、それぞれが前のものよりも機能が増しています。

- **OCR/読み取り**: 構造や意味を解釈せずにドキュメントから生のテキストを抽出します。「ここにはどんなテキストがあるか？」という問いに答えます。
- **レイアウト**: テーブルを含む構造、階層、位置情報を取得します。「このコンテンツはどのように整理されているか？」という問いに答えます。
- **ドキュメントのフィールド**: フィールドを抽出し体系的なカテゴリに整理して洞察を生成する機能を組み合わせたアナライザー。「このコンテンツは何を意味し、どうすべきか？」という問いに答えます。このような Content Understanding アナライザーは、複雑な抽出ニーズを処理するために（チャット補完モデルや埋め込みモデルなど）追加の AI モデルのデプロイが必要な場合があります。

また、開発者が **Python SDK** を使用して Content Understanding をアプリケーションに統合する方法も学びました。Foundry プレイグラウンドの外でドキュメントをプログラムで分析できます。
