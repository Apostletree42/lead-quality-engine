import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

class LeadScorer:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=10)
        self.scaler = StandardScaler()
        self.feature_columns = [
            'email_quality', 'phone_quality', 'title_value', 
            'data_completeness', 'industry_fit'
        ]
        self.is_trained = False
        
    def create_training_labels(self, df):
        """
        Create synthetic training labels based on business logic
        (In real world, we use actual conversion data)
        """
        labels = []
        
        for _, row in df.iterrows():
            # Start with base score
            score = 0.0
            
            # High-value combinations get bonus points
            if row['email_quality'] >= 0.8 and row['title_value'] >= 0.8:
                score += 0.4  # Good email + decision maker
                
            if row['data_completeness'] >= 0.75:
                score += 0.3  # Complete profile
                
            if row['industry_fit'] >= 0.9:
                score += 0.2  # Perfect industry match
                
            if row['phone_quality'] >= 0.8:
                score += 0.1  # Valid phone number
                
            # Add some realistic noise
            score += np.random.normal(0, 0.05)
            score = np.clip(score, 0, 1)
            
            # Convert to binary classification (good lead vs poor lead)
            labels.append(1 if score > 0.6 else 0)
            
        return np.array(labels)
    
    def train(self, df):
        """Train the model on processed lead data"""
        
        # Prepare features
        X = df[self.feature_columns].values
        y = self.create_training_labels(df)
        
        # Split for validation
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        
        # Calculate accuracy
        train_accuracy = self.model.score(X_train_scaled, y_train)
        test_accuracy = self.model.score(X_test_scaled, y_test)
        
        self.is_trained = True
        
        return {
            'train_accuracy': train_accuracy,
            'test_accuracy': test_accuracy,
            'total_samples': len(df),
            'positive_leads': sum(y)
        }
    
    def predict_scores(self, df):
        """Predict lead quality scores (0-1 probability)"""
        if not self.is_trained:
            raise ValueError("Model must be trained first!")
            
        X = df[self.feature_columns].values
        X_scaled = self.scaler.transform(X)
        
        # Get probability of being a good lead
        probabilities = self.model.predict_proba(X_scaled)[:, 1]
        
        return probabilities
    
    def categorize_leads(self, scores):
        """Convert scores to business categories"""
        categories = []
        for score in scores:
            if score >= 0.8:
                categories.append("Hot Lead")
            elif score >= 0.6:
                categories.append("Warm Lead")
            elif score >= 0.4:
                categories.append("Cold Lead")
            else:
                categories.append("Low Priority")
        return categories
    
    def get_feature_importance(self):
        """Get which features matter most for scoring"""
        if not self.is_trained:
            return {}
            
        importance_dict = {}
        for name, importance in zip(self.feature_columns, self.model.feature_importances_):
            importance_dict[name] = round(importance, 3)
        
        # Sort by importance
        return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
    
    def explain_score(self, lead_data):
        """Explain why a lead got its score"""
        explanations = []
        
        if lead_data['email_quality'] >= 0.8:
            explanations.append("Valid business email")
        elif lead_data['email_quality'] <= 0.3:
            explanations.append("Missing or poor email")
            
        if lead_data['title_value'] >= 0.8:
            explanations.append("Decision maker role")
        elif lead_data['title_value'] <= 0.3:
            explanations.append("Low-influence role")
            
        if lead_data['data_completeness'] >= 0.75:
            explanations.append("Complete contact info")
        else:
            explanations.append("Missing contact details")
            
        return explanations