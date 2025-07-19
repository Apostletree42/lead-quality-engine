import pandas as pd
import sys
import os

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from data_processor import LeadProcessor

# Test the processor
print("🧪 Testing Lead Processor...")

# Load sample data
df = pd.read_csv('data/sample_leads.csv')
print(f"✅ Loaded {len(df)} leads")

# Process the data
processor = LeadProcessor()
processed_df = processor.process_leads(df)

print(f"\n📊 New features added:")
new_features = ['email_quality', 'phone_quality', 'title_value', 'data_completeness', 'industry_fit']
for feature in new_features:
    avg_score = processed_df[feature].mean()
    print(f"  - {feature}: {avg_score:.2f} (average)")

print(f"\n🎯 Sample processed leads:")
print(processed_df[['Company', 'Contact_Name', 'email_quality', 'title_value', 'data_completeness']].head())

print(f"\n✅ Processing complete! Ready for model training.")