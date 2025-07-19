import pandas as pd
import json
import sys
import os

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from hubspot_formatter import HubSpotFormatter

print("🔗 Testing HubSpot Integration...")

# Load enhanced data from previous step
df = pd.read_csv('data/enhanced_leads.csv')
print(f"✅ Loaded {len(df)} enhanced leads")

# Initialize HubSpot formatter
formatter = HubSpotFormatter()

# Test contact formatting
hubspot_data = formatter.format_for_hubspot(df)

print(f"\n📊 HubSpot Import Summary:")
summary = hubspot_data['summary']
print(f"  - Total Contacts: {summary['total_contacts']}")
print(f"  - Hot Leads: {summary['hot_leads']}")
print(f"  - Import Date: {summary['import_date']}")
print(f"  - Source: {summary['source']}")

# Show sample formatted contact
if hubspot_data['contacts']:
    print(f"\n👤 Sample HubSpot Contact:")
    sample_contact = hubspot_data['contacts'][0]
    for key, value in sample_contact.items():
        if value:  # Only show non-empty fields
            print(f"  - {key}: {value}")

# Test workflow recommendations
workflows = formatter.generate_recommended_workflows(df)
print(f"\n⚡ Recommended HubSpot Workflows:")
for i, workflow in enumerate(workflows, 1):
    print(f"  {i}. {workflow['name']}")
    print(f"     Trigger: {workflow['trigger']}")
    print(f"     Affects: {workflow['affected_leads']} leads")
    print(f"     Actions: {len(workflow['actions'])} automated steps")

# Test task generation
tasks = formatter.create_sales_tasks(df)
print(f"\n✅ Sales Tasks Generated: {len(tasks)}")
if tasks:
    print(f"  High Priority: {len([t for t in tasks if t['priority'] == 'High'])}")
    print(f"  Medium Priority: {len([t for t in tasks if t['priority'] == 'Medium'])}")
    
    print(f"\n📋 Top 3 Tasks:")
    for i, task in enumerate(tasks[:3], 1):
        print(f"  {i}. {task['title']} ({task['priority']} - due in {task['due_date']})")

# Save HubSpot import file
with open('data/hubspot_import.json', 'w') as f:
    json.dump(hubspot_data, f, indent=2)

print(f"\n💾 Saved HubSpot import file: data/hubspot_import.json")

# Save tasks as CSV for easy viewing
if tasks:
    tasks_df = pd.DataFrame(tasks)
    tasks_df.to_csv('data/sales_tasks.csv', index=False)
    print(f"💾 Saved sales tasks: data/sales_tasks.csv")

print(f"\n🎯 Integration Summary:")
print(f"  - {len(hubspot_data['contacts'])} contacts ready for HubSpot import")
print(f"  - {len(workflows)} automated workflows suggested")
print(f"  - {len(tasks)} prioritized tasks created")
print(f"  - Custom properties: ai_lead_score, lead_priority, data_completeness_score")

print(f"\n✅ HubSpot integration testing complete!")