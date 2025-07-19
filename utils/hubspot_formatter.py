import pandas as pd
from datetime import datetime

class HubSpotFormatter:
    """Simple HubSpot integration layer for lead quality data"""
    
    def __init__(self):
        self.lead_score_property = 'ai_lead_score'
        self.lead_category_property = 'lead_quality_category'
        
    def format_for_hubspot(self, df):
        """Convert enhanced leads to HubSpot import format"""
        
        hubspot_contacts = []
        
        for _, row in df.iterrows():
            # Only create contacts with valid email or phone
            if self._has_contact_info(row):
                contact = self._format_contact(row)
                hubspot_contacts.append(contact)
        
        return {
            'contacts': hubspot_contacts,
            'summary': {
                'total_contacts': len(hubspot_contacts),
                'hot_leads': len([c for c in hubspot_contacts if c.get('lead_priority') == 'High']),
                'import_date': datetime.now().strftime('%Y-%m-%d'),
                'source': 'SaaSSquatch + AI Enhancement'
            }
        }
    
    def _format_contact(self, row):
        """Format single lead for HubSpot contact"""
        
        # Parse contact name
        first_name, last_name = self._parse_name(row.get('Contact_Name', ''))
        
        # Convert lead score to 0-100 scale for HubSpot
        lead_score_100 = round(row.get('lead_score', 0) * 100)
        
        contact = {
            # Standard HubSpot contact properties
            'email': row.get('Contact_Email') if row.get('Contact_Email') != 'N/A' else '',
            'firstname': first_name,
            'lastname': last_name,
            'jobtitle': row.get('Contact_Title') if row.get('Contact_Title') != 'N/A' else '',
            'phone': row.get('Contact_Phone') if row.get('Contact_Phone') != 'N/A' else '',
            'company': row.get('Company', ''),
            'website': row.get('Website') if row.get('Website') != 'N/A' else '',
            'city': row.get('City', ''),
            'state': row.get('State', ''),
            
            # Custom properties for lead quality
            'ai_lead_score': lead_score_100,
            'lead_quality_category': row.get('category', ''),
            'lead_priority': self._get_priority_level(row.get('lead_score', 0)),
            'data_completeness_score': round(row.get('data_completeness', 0) * 100),
            'lead_source': 'SaaSSquatch Enhanced',
            'last_updated': datetime.now().strftime('%Y-%m-%d')
        }
        
        return contact
    
    def generate_recommended_workflows(self, df):
        """Suggest HubSpot workflows based on lead scores"""
        
        workflows = []
        
        # Count leads by category
        hot_count = len(df[df['lead_score'] >= 0.8])
        warm_count = len(df[(df['lead_score'] >= 0.6) & (df['lead_score'] < 0.8)])
        
        if hot_count > 0:
            workflows.append({
                'name': 'Hot Lead Immediate Follow-up',
                'trigger': 'AI Lead Score >= 80',
                'actions': [
                    'Create high-priority task for sales rep',
                    'Send Slack notification to sales team',
                    'Set lifecycle stage to "Sales Qualified Lead"'
                ],
                'affected_leads': hot_count
            })
        
        if warm_count > 0:
            workflows.append({
                'name': 'Warm Lead Nurture Sequence',
                'trigger': 'AI Lead Score 60-79',
                'actions': [
                    'Enroll in email nurture campaign',
                    'Create follow-up task in 3 days',
                    'Add to "Warm Prospects" list'
                ],
                'affected_leads': warm_count
            })
        
        return workflows
    
    def create_sales_tasks(self, df):
        """Generate prioritized task list for sales team"""
        
        tasks = []
        
        # Sort by lead score, focus on top leads
        top_leads = df.nlargest(10, 'lead_score')
        
        for _, lead in top_leads.iterrows():
            score = lead.get('lead_score', 0)
            company = lead.get('Company', 'Unknown Company')
            contact = lead.get('Contact_Name', 'Unknown Contact')
            
            if score >= 0.8:
                task = {
                    'title': f'URGENT: Call {company}',
                    'description': f'Hot lead ({score*100:.0f}% score). Contact: {contact}',
                    'priority': 'High',
                    'due_date': '1 day',
                    'task_type': 'call'
                }
            elif score >= 0.6:
                task = {
                    'title': f'Research and reach out to {company}',
                    'description': f'Warm lead ({score*100:.0f}% score). Research before calling.',
                    'priority': 'Medium',
                    'due_date': '3 days',
                    'task_type': 'research'
                }
            else:
                continue  # Skip low-priority leads for task list
                
            tasks.append(task)
        
        return tasks
    
    def _has_contact_info(self, row):
        """Check if lead has enough info to be worth importing"""
        has_email = row.get('Contact_Email') and row.get('Contact_Email') != 'N/A'
        has_phone = row.get('Contact_Phone') and row.get('Contact_Phone') != 'N/A'
        return has_email or has_phone
    
    def _parse_name(self, full_name):
        """Split full name into first and last name"""
        if pd.isna(full_name) or full_name == 'N/A':
            return '', ''
        
        parts = str(full_name).strip().split(' ', 1)
        first_name = parts[0] if parts else ''
        last_name = parts[1] if len(parts) > 1 else ''
        
        return first_name, last_name
    
    def _get_priority_level(self, score):
        """Convert score to business priority level"""
        if score >= 0.8:
            return 'High'
        elif score >= 0.6:
            return 'Medium'
        else:
            return 'Low'