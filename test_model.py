import pandas as pd
import sys
import os

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'models'))

from data_processor import LeadProcessor
from lead_scorer import LeadScorer

print("🤖 Testing Lead Scoring Model...")

# Load and process data
df = pd.read_csv('data/sample_leads.csv')
processor = LeadProcessor()
processed_df = processor.process_leads(df)

print(f"✅ Processed {len(processed_df)} leads")

# Train the model
scorer = LeadScorer()
training_results = scorer.train(processed_df)

print(f"\n📊 Training Results:")
print(f"  - Train Accuracy: {training_results['train_accuracy']:.2%}")
print(f"  - Test Accuracy: {training_results['test_accuracy']:.2%}")
print(f"  - Good Leads Found: {training_results['positive_leads']}/{training_results['total_samples']}")

# Generate scores
scores = scorer.predict_scores(processed_df)
processed_df['lead_score'] = scores
processed_df['category'] = scorer.categorize_leads(scores)

print(f"\n🎯 Score Distribution:")
print(f"  - Average Score: {scores.mean():.2f}")
print(f"  - Score Range: {scores.min():.2f} - {scores.max():.2f}")

print(f"\n📈 Lead Categories:")
category_counts = processed_df['category'].value_counts()
for category, count in category_counts.items():
    print(f"  - {category}: {count}")

print(f"\n🏆 Top 5 Leads:")
top_leads = processed_df.nlargest(5, 'lead_score')[['Company', 'Contact_Name', 'lead_score', 'category']]
print(top_leads.to_string(index=False))

print(f"\n🔍 Feature Importance:")
importance = scorer.get_feature_importance()
for feature, imp in importance.items():
    print(f"  - {feature}: {imp}")

# Test explanation for top lead
if len(processed_df) > 0:
    top_lead = processed_df.iloc[processed_df['lead_score'].idxmax()]
    explanations = scorer.explain_score(top_lead)
    print(f"\n💡 Why '{top_lead['Company']}' scored high:")
    for explanation in explanations:
        print(f"  {explanation}")

print(f"\n✅ Model testing complete!")

# Save enhanced dataset for next step
processed_df.to_csv('data/enhanced_leads.csv', index=False)
print(f"💾 Saved enhanced dataset with scores")