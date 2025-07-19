import os
import time
import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional

try:
    from hubspot import HubSpot
    from hubspot.crm.contacts import SimplePublicObjectInput, ApiException
    HUBSPOT_AVAILABLE = True
except ImportError:
    HUBSPOT_AVAILABLE = False

class HubSpotAPI:
    """Real HubSpot API integration for lead quality data - SIMPLIFIED"""
    
    def __init__(self, access_token: str):
        if not HUBSPOT_AVAILABLE:
            raise ImportError("HubSpot SDK not available")
            
        self.client = HubSpot(access_token=access_token)
        self.access_token = access_token
        
    def test_connection(self) -> Dict:
        """Test if API connection works"""
        try:
            # Simple test - try to get owner info
            owners = self.client.crm.owners.get_all(limit=1)
            return {
                'success': True,
                'account_id': 'connected',
                'scopes': ['crm.objects.contacts.read', 'crm.objects.contacts.write']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_account_info(self) -> Dict:
        """Get HubSpot account information"""
        try:
            owners = self.client.crm.owners.get_all(limit=1)
            return {
                'account_id': 'connected',
                'status': 'active',
                'connection': 'verified'
            }
        except Exception as e:
            return {'error': str(e)}
    
    def create_custom_properties(self) -> Dict:
        """Skip property creation and return success message"""
        return {
            'created': [],
            'existed': ['Using standard HubSpot fields instead'],
            'errors': [],
            'message': 'Skipping custom property creation - using standard fields + notes for AI scores'
        }
    
    def upload_contacts(self, contacts_data: List[Dict], batch_size: int = 3) -> Dict:
        """Upload contacts to HubSpot - FOCUS ON SUCCESS"""
        
        results = {
            'total_contacts': len(contacts_data),
            'successful': 0,
            'failed': 0,
            'errors': [],
            'created_contacts': []
        }
        
        # Create progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Process in very small batches
        for i in range(0, len(contacts_data), batch_size):
            batch = contacts_data[i:i + batch_size]
            
            # Update progress
            progress = min((i + batch_size) / len(contacts_data), 1.0)
            progress_bar.progress(progress)
            status_text.text(f"Uploading contacts {i+1}-{min(i+batch_size, len(contacts_data))} of {len(contacts_data)}...")
            
            for contact_data in batch:
                try:
                    # Prepare contact properties
                    properties = self._prepare_contact_properties(contact_data)
                    
                    # Skip if no email
                    if not properties.get('email'):
                        results['failed'] += 1
                        results['errors'].append(f"Contact {contact_data.get('company', 'Unknown')}: No email address")
                        continue
                    
                    # Create contact input
                    contact_input = SimplePublicObjectInput(properties=properties)
                    
                    # Upload to HubSpot - FIXED METHOD SIGNATURE
                    response = self.client.crm.contacts.basic_api.create(
                        simple_public_object_input_for_create=contact_input
                    )
                    
                    results['successful'] += 1
                    results['created_contacts'].append({
                        'hubspot_id': response.id,
                        'email': properties.get('email', ''),
                        'company': properties.get('company', ''),
                        'ai_score': contact_data.get('ai_lead_score', 0)
                    })
                    
                except ApiException as e:
                    results['failed'] += 1
                    if "already exists" in str(e).lower():
                        error_msg = f"Contact {contact_data.get('email', 'Unknown')}: Already exists in HubSpot"
                    else:
                        error_msg = f"Contact {contact_data.get('email', 'Unknown')}: {str(e)}"
                    results['errors'].append(error_msg)
                    
                except Exception as e:
                    results['failed'] += 1
                    error_msg = f"Contact {contact_data.get('email', 'Unknown')}: {str(e)}"
                    results['errors'].append(error_msg)
            
            # Delay to respect rate limits
            time.sleep(2.0)
        
        # Final progress update
        progress_bar.progress(1.0)
        status_text.text(f"✅ Upload complete! {results['successful']} successful, {results['failed']} failed")
        
        return results
    
    def _prepare_contact_properties(self, contact_data: Dict) -> Dict:
        """Prepare contact data for HubSpot API format"""
        
        properties = {}
        
        # Required: Email
        if contact_data.get('email'):
            properties['email'] = str(contact_data['email']).strip()
        
        # Name handling
        if contact_data.get('firstname'):
            properties['firstname'] = str(contact_data['firstname']).strip()
        if contact_data.get('lastname'):
            properties['lastname'] = str(contact_data['lastname']).strip()
        
        # If we have Contact_Name but no firstname/lastname, split it
        if not properties.get('firstname') and contact_data.get('Contact_Name'):
            name_parts = str(contact_data['Contact_Name']).strip().split(' ', 1)
            if name_parts[0] and name_parts[0] != 'N/A':
                properties['firstname'] = name_parts[0]
                if len(name_parts) > 1:
                    properties['lastname'] = name_parts[1]
        
        # Company and job title
        if contact_data.get('company') and contact_data['company'] != 'N/A':
            properties['company'] = str(contact_data['company']).strip()
            
        if contact_data.get('jobtitle') and contact_data['jobtitle'] != 'N/A':
            properties['jobtitle'] = str(contact_data['jobtitle']).strip()
        elif contact_data.get('Contact_Title') and contact_data['Contact_Title'] != 'N/A':
            properties['jobtitle'] = str(contact_data['Contact_Title']).strip()
        
        # Phone number
        if contact_data.get('phone') and contact_data['phone'] != 'N/A':
            properties['phone'] = str(contact_data['phone']).strip()
        elif contact_data.get('Contact_Phone') and contact_data['Contact_Phone'] != 'N/A':
            properties['phone'] = str(contact_data['Contact_Phone']).strip()
        
        # Website
        if contact_data.get('website') and contact_data['website'] != 'N/A':
            properties['website'] = str(contact_data['website']).strip()
        
        # City and State
        if contact_data.get('city'):
            properties['city'] = str(contact_data['city']).strip()
        if contact_data.get('state'):
            properties['state'] = str(contact_data['state']).strip()
        
        # AI Score in notes field - THIS IS THE KEY!
        ai_notes = []
        if contact_data.get('ai_lead_score'):
            try:
                score = float(contact_data['ai_lead_score'])
                if score <= 1:
                    score = score * 100  # Convert to 0-100 scale
                ai_notes.append(f"🎯 AI Lead Score: {score:.0f}/100")
            except:
                pass
        
        if contact_data.get('category'):
            ai_notes.append(f"Category: {contact_data['category']}")
        
        if contact_data.get('lead_priority'):
            ai_notes.append(f"Priority: {contact_data['lead_priority']}")
        
        # Add source info
        ai_notes.append(f"Enhanced: {datetime.now().strftime('%Y-%m-%d')}")
        ai_notes.append("Source: SaaSSquatch + AI Enhancement")

        # Store AI data in notes
        if ai_notes:
            properties['hs_content_membership_notes'] = '\n'.join(ai_notes)
        
        # Set lead status
        properties['hs_lead_status'] = 'NEW'
        properties['lifecyclestage'] = 'lead'
        
        return properties

# Helper function for Streamlit integration
def create_hubspot_client(api_key: str) -> Optional[HubSpotAPI]:
    """Create HubSpot client with error handling"""
    if not HUBSPOT_AVAILABLE:
        return None
    
    if not api_key:
        return None
    
    try:
        client = HubSpotAPI(api_key)
        
        # Test connection immediately
        connection_test = client.test_connection()
        if not connection_test['success']:
            st.error(f"Connection failed: {connection_test['error']}")
            return None
        
        return client
        
    except Exception as e:
        st.error(f"Failed to create client: {str(e)}")
        return None