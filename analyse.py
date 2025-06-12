import pandas as pd
import json
import nltk
import matplotlib.pyplot as plt
import seaborn as sns
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords

# Initialisation des outils NLTK
nltk.download('vader_lexicon')
nltk.download('stopwords')
sia = SentimentIntensityAnalyzer()
stop_words = stopwords.words('french') + ['crypto', 'cryptomonnaie', 'cryptos']

# Liste des mots-clés à détecter
keywords = [
    'gains', 'opportunités', 'liberté financière', 'nft', 'web3', 'blockchain',
    'investissement', 'bull run', 'bitcoin', 'gagner', 'investir', 'etf', 'liberté',
    'bull market', 'régulation', 'crash', 'peur'
]

# Fonctions
def clean_messages(df):
    df['message_clean'] = df['message'].str.lower()
    return df

def detect_keywords(df, keywords):
    for kw in keywords:
        df[f'contains_{kw}'] = df['message_clean'].str.contains(kw, regex=False, na=False)
    return df

def compute_sentiment(df):
    df['sentiment_score'] = df['message_clean'].apply(lambda x: sia.polarity_scores(x)['compound'])
    df['sentiment_label'] = pd.cut(df['sentiment_score'], bins=[-1, -0.05, 0.05, 1],
                                   labels=['négatif', 'neutre', 'positif'])
    return df

def plot_sentiment_distribution(df):
    sns.countplot(data=df, x='sentiment_label')
    plt.title('Distribution des sentiments dans les messages crypto')
    plt.show()

def analyze_temporal_keywords(df):
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['contains_bull_market'] = df['message_clean'].str.contains('bull market', na=False)
    df['contains_regulation'] = df['message_clean'].str.contains('régulation', na=False)
    df_monthly = df.set_index('date').resample('M').agg({
        'contains_bull_market': 'sum',
        'contains_regulation': 'sum'
    }).reset_index()

    plt.figure(figsize=(12, 6))
    sns.lineplot(data=df_monthly, x='date', y='contains_bull_market', label='Bull Market')
    sns.lineplot(data=df_monthly, x='date', y='contains_regulation', label='Régulation')
    plt.title('Volume de messages par mois autour d’événements clés')
    plt.xlabel('Date')
    plt.ylabel('Nombre de messages')
    plt.legend()
    plt.show()

def run_analysis(df):
    df = clean_messages(df)
    df = detect_keywords(df, keywords)
    print("Fréquence des mots-clés :")
    print(df[[f'contains_{kw}' for kw in keywords]].sum().sort_values(ascending=False))
    df = compute_sentiment(df)
    plot_sentiment_distribution(df)
    analyze_temporal_keywords(df)

# Fonction principale
def main():
    # Charger les données JSON
    fichier_json = 'all_crypto_groups_messages.json'
    with open(fichier_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Extraire tous les messages
    messages = []
    for groupe in data:
        for msg in groupe.get("messages", []):
            msg['group_name'] = groupe.get("group_name")
            msg['group_id'] = groupe.get("group_id")
            msg['member_count'] = groupe.get("member_count")
            messages.append(msg)

    df = pd.DataFrame(messages)

    # Nettoyage des colonnes inutiles
    colonnes_a_supprimer = [
        "id", "sender_id", "first_name", "last_name",
        "username", "media_type", "media_path", "reply_to"
    ]
    df.drop(columns=colonnes_a_supprimer, inplace=True, errors='ignore')

    # Conversion date
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # Graphique des messages par jour et groupe
    messages_par_jour = df.groupby(['group_name', df['date'].dt.date]).size().reset_index(name='n_messages')
    messages_par_jour['date'] = pd.to_datetime(messages_par_jour['date'])

    plt.figure(figsize=(14, 7))
    sns.lineplot(data=messages_par_jour, x='date', y='n_messages', hue='group_name', marker='o')
    plt.title("Nombre de messages par jour par groupe Telegram")
    plt.xlabel("Date")
    plt.ylabel("Nombre de messages")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.legend(title='Nom du groupe')
    plt.tight_layout()
    plt.show()

    # Analyse des liens
    df['contient_lien'] = df['message'].str.contains(r'https?://', na=False)
    df['plateforme'] = df['message'].str.extract(r'(t\.me|twitter\.com|youtube\.com|instagram\.com|discord\.gg)', expand=False)

    plateformes = df['plateforme'].value_counts()
    print("=== Plateformes les plus citées ===")
    print(plateformes)

    # Barplot
    plt.figure(figsize=(10, 6))
    sns.barplot(x=plateformes.index, y=plateformes.values, palette='viridis')
    plt.title("Fréquence des liens vers d'autres plateformes")
    plt.show()

    # Statistiques par groupe
    liens_par_groupe = df.groupby('group_name')['contient_lien'].sum().reset_index(name='nb_messages_avec_lien')
    total_par_groupe = df.groupby('group_name').size().reset_index(name='nb_total_messages')
    analyse_liens = pd.merge(liens_par_groupe, total_par_groupe, on='group_name')
    analyse_liens['%_messages_avec_lien'] = 100 * analyse_liens['nb_messages_avec_lien'] / analyse_liens['nb_total_messages']

    plateformes_par_groupe = df.groupby(['group_name', 'plateforme']).size().reset_index(name='nb_messages_plateforme').dropna()

    print("\n=== Pourcentage de messages avec lien par groupe ===")
    print(analyse_liens.sort_values('%_messages_avec_lien', ascending=False))

    print("\n=== Répartition des plateformes par groupe ===")
    print(plateformes_par_groupe.sort_values(['group_name', 'nb_messages_plateforme'], ascending=[True, False]))

    # Lancer l'analyse de contenu
    run_analysis(df)

# Lancer le script
if __name__ == "__main__":
    main()
