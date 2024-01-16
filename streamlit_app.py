import streamlit as st
import requests

# Streamlit UI components
st.title('RMI in a Box')
uid = st.text_input('Enter your name (so the robot remembers your conversation):')
query = st.text_input('Enter your query:')
submit_button = st.button('Ask')

if submit_button:
    # Making a POST request to your FastAPI endpoint
    response = requests.post(
        'https://rmi-in-a-box.politemushroom-551f150f.westus2.azurecontainerapps.io/ask',  # Replace with your FastAPI URL
        json={'uid': uid, 'query': query}
    )

    if response.status_code == 200:
        data = response.json()
        st.write('Answer:', data['answer'])
        st.write('Sources:', data['sources'])
    else:
        st.write('Error:', response.text)