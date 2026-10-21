---
lab:
  title: 演習環境準備 - Microsoft Foundry プロジェクトの作成
  description: Microsoft Foundry プロジェクトを作成し、演習環境を準備します。
  level: 200
  duration: 10 minutes
  islab: true
  primarytopics:
    - Microsoft Foundry
---

# 演習環境準備: Microsoft Foundry プロジェクトの作成

この演習では、Microsoft Foundry プロジェクトを作成して演習環境を準備します。このプロジェクトは後続のすべての演習で使用します。

この演習の完了には約 **10** 分かかります。

> **注**: Microsoft Foundry ポータルを含む Microsoft Foundry の多くのコンポーネントは継続的に開発されています。これは人工知能技術の急速な進歩を反映しています。ユーザー エクスペリエンスの一部の要素が、この演習の画像や説明と異なる場合があります。

## Azure Portalへのサインイン

Microsoft Foundryでの操作を実施する前に、Azure Portalへのサインインを実施して多要素認証(MFA)の設定を実施します。現在、Microsoft Foundryを使用自体にはMFAを要求されませんが、Foundryプロジェクトおよびそのリソースを作成するためには、MFA設定済みのユーザーを使用する必要があります。

1.  Web ブラウザーをInPrivateウィンドウ（シークレットウィンドウ）で開き、[Azure Portal](https://portal.azure.com/)にアクセスします。
2. ユーザー名、パスワードは講師から配布されたAzureの資格情報を使用してサインインを実施します。
3. **アカウントをセキュリティ保護しましょう** が表示されたら、指示に従って **Microsoft Authenticator** を使用した多要素認証の登録を進めます。
   お手持ちのスマートフォンにインストールされたMicrosoft AuthenticatorにてQRコードを読み取ります。QRコードは **次へ** を数回クリックすると表示されます。
4. スマートフォン上にアカウント情報が登録されたらQRコードが表示されているブラウザ画面で **次へ** をクリックして、表示された数字をスマートフォンに通知された画面で入力してMFA登録を完了します。
5. **Authenticator Added** と表示されれば作業は完了です。途中でタイムアウトなどで失敗する場合は、一度ウィンドウを閉じてAzure Portalへのアクセス、サインインから再度実行します。

## Microsoft Foundry プロジェクトの作成

Microsoft Foundry は *プロジェクト* を使用して、AI ソリューションの開発に使用するモデル、リソース、データ、その他のアセットを整理します。プロジェクトは Azure の *Microsoft Foundry* リソースに関連付けられており、Azure 上での AI アプリとエージェント開発をサポートするために必要なクラウド サービスを提供します。

1. Web ブラウザーで新しいタブをInPrivateウィンドウ（シークレットウィンドウ）で開き、 <a href="https://ai.azure.com" target="_blank">Microsoft Foundry</a> (https://ai.azure.com)にアクセスします。

    画面右上にある　**[Sign in]** をクリックして、Azure の資格情報を使用してサインインします。 

1. 自動でリソースおよびプロジェクトの作成が開始されるため、プロジェクトの作成完了まで待ちます（数分かかる場合があります）。新しい Foundry ポータルでプロジェクトを作成または選択すると、次の画像のようなページが表示されます。

    > MFA（多要素認証）に関するエラーが表示される場合があります。一度MFAを通す必要があるため、プロジェクトを設定する画面を閉じ、右上に表示されるポップアップからMFAでの認証を実施してください。

    ![Foundry プロジェクト ホーム ページのスクリーンショット。](./media/foundry-home.JPG)

## まとめ

Microsoft Foundry プロジェクトの作成が完了しました。このプロジェクトは後続のすべての演習で使用します。次の演習に進んでください。
