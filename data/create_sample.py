import pandas as pd
import random

# Create realistic sample data matching SaaSSquatch format
companies = [
    "TechFlow Solutions", "DataSync Inc", "CloudPipe Pro", "DevCore Ltd",
    "AI Metrics Co", "SaaS Builder", "Growth Labs", "Pipeline Tech",
    "CodeStream", "AutoScale", "DataBridge", "CloudForge"
]

industries = ["Computer Software Developers", "Technology", "SaaS", "Consulting", "Marketing"]
states = ["CA", "NY", "TX", "FL", "WA", "NJ", "PA"]
cities = ["San Francisco", "New York", "Austin", "Miami", "Seattle", "Boston", "Denver"]

# Generate 100 sample leads (smaller dataset for faster processing)
data = []
for i in range(100):
    company_base = random.choice(companies)
    company = f"{company_base} {random.choice(['Inc', 'LLC', 'Corp', 'Co'])}"
    
    # Some realistic missing data patterns
    has_email = random.random() > 0.3  # 70% have emails
    has_phone = random.random() > 0.4  # 60% have phones  
    has_contact = random.random() > 0.2  # 80% have contact names
    
    data.append({
        'Company': company,
        'Industry': random.choice(industries),
        'Street': f"{random.randint(100,9999)} {random.choice(['Main St', 'Oak Ave', 'Tech Blvd', 'Innovation Dr'])}",
        'City': random.choice(cities),
        'State': random.choice(states),
        'BBB_Rating': random.choice(['A+', 'A', 'B+', 'B', 'N/A', 'N/A']),  # More N/A for realism
        'Company_Phone': f"({random.randint(200,999)}) {random.randint(200,999)}-{random.randint(1000,9999)}" if has_phone else "N/A",
        'Website': f"www.{company.lower().replace(' ', '').replace(',', '')}.com" if random.random() > 0.15 else "N/A",
        'Contact_Name': f"{random.choice(['John', 'Jane', 'Mike', 'Sarah', 'David', 'Lisa'])} {random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Davis'])}" if has_contact else "N/A",
        'Contact_Title': random.choice(['CEO', 'CTO', 'VP Sales', 'Marketing Director', 'Founder', 'President', 'Manager', 'N/A']),
        'Contact_Email': f"contact{i}@{company.lower().replace(' ', '').replace(',', '')}.com" if has_email else "N/A",
        'Contact_Phone': f"({random.randint(200,999)}) {random.randint(200,999)}-{random.randint(1000,9999)}" if random.random() > 0.5 else "N/A"
    })

df = pd.DataFrame(data)
df.to_csv('data/sample_leads.csv', index=False)
print(f"✅ Created {len(df)} sample leads")
print("\nSample data preview:")
print(df.head(3))
print(f"\nMissing data summary:")
print(df.isnull().sum() + (df == "N/A").sum())