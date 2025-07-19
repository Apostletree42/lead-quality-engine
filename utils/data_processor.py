import pandas as pd
import re

class LeadProcessor:
    def __init__(self):
        # Define what makes a "good" lead based on startup experience
        self.decision_maker_titles = ['ceo', 'cto', 'vp', 'director', 'founder', 'president']
        self.tech_industries = ['software', 'technology', 'saas', 'tech']
    
    def process_leads(self, df):
        """Add quality features to raw lead data"""
        df_processed = df.copy()
        
        # Core quality features
        df_processed['email_quality'] = df['Contact_Email'].apply(self._score_email)
        df_processed['phone_quality'] = df['Contact_Phone'].apply(self._score_phone)
        df_processed['title_value'] = df['Contact_Title'].apply(self._score_title)
        df_processed['data_completeness'] = self._calculate_completeness(df)
        df_processed['industry_fit'] = df['Industry'].apply(self._score_industry)
        
        return df_processed
    
    def _score_email(self, email):
        """Score email quality (0-1)"""
        if pd.isna(email) or email == "N/A":
            return 0.0
        
        # Basic email validation
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return 0.2
        
        # Business email > personal email
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        domain = email.split('@')[1].lower()
        
        return 0.6 if domain in personal_domains else 1.0
    
    def _score_phone(self, phone):
        """Score phone availability (0-1)"""
        if pd.isna(phone) or phone == "N/A":
            return 0.0
        
        # Clean and check phone format
        digits = re.sub(r'[^\d]', '', phone)
        if len(digits) in [10, 11]:  # Valid US phone number
            return 1.0
        return 0.3
    
    def _score_title(self, title):
        """Score contact title importance (0-1)"""
        if pd.isna(title) or title == "N/A":
            return 0.0
        
        title_lower = title.lower()
        
        # High-value decision makers
        for key_title in self.decision_maker_titles:
            if key_title in title_lower:
                return 1.0
        
        # Medium value (managers, etc.)
        if any(word in title_lower for word in ['manager', 'lead', 'head']):
            return 0.6
            
        return 0.3  # Other titles
    
    def _calculate_completeness(self, df):
        """Calculate how complete each lead's data is (0-1)"""
        completeness_scores = []
        
        key_fields = ['Contact_Email', 'Contact_Phone', 'Contact_Name', 'Website']
        
        for _, row in df.iterrows():
            filled_count = 0
            for field in key_fields:
                if not pd.isna(row[field]) and row[field] != "N/A":
                    filled_count += 1
            
            completeness_scores.append(filled_count / len(key_fields))
        
        return completeness_scores
    
    def _score_industry(self, industry):
        """Score industry alignment (0-1)"""
        if pd.isna(industry):
            return 0.5
        
        industry_lower = industry.lower()
        
        # Tech companies are high priority for our use case
        for tech_keyword in self.tech_industries:
            if tech_keyword in industry_lower:
                return 1.0
        
        return 0.7  # Other industries still valuable