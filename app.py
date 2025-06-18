import pandas as pd
import joblib
import os
from flask import Flask, request, jsonify, render_template_string # Import render_template_string
import nest_asyncio # Still useful if testing parts of the notebook or local dev that might conflict

# Apply nest_asyncio for compatibility
nest_asyncio.apply()

# --- Configuration ---
# Define paths to your model files relative to app.py.
# Assuming app.py is in the project root and models/ is a direct subdirectory.
MODEL_PATH = os.path.join('models', 'personality_model.joblib')
LABEL_ENCODER_PATH = os.path.join('models', 'personality_label_encoder.joblib')

# --- Load Model and Encoder ---
loaded_model = None
loaded_le_personality = None

try:
    loaded_model = joblib.load(MODEL_PATH)
    loaded_le_personality = joblib.load(LABEL_ENCODER_PATH)
    print(f"Model loaded successfully from {MODEL_PATH}")
    print(f"Label Encoder loaded successfully from {LABEL_ENCODER_PATH}")
except FileNotFoundError:
    print(f"Error: Model files not found at '{MODEL_PATH}' or '{LABEL_ENCODER_PATH}'.")
    print("Please ensure the 'models/' directory exists in the project root and contains the '.joblib' files.")
    print("You need to train the model first by running the `introvert_extrovert_predictor.ipynb` notebook to generate these files.")
    # In a production scenario, you might want to exit the application here if models are crucial.
except Exception as e:
    print(f"An unexpected error occurred while loading model files: {e}")

# --- Initialize Flask App ---
app = Flask(__name__)

# --- Root Route for Browser Access (GET request) ---
@app.route('/', methods=['GET'])
def home():
    """
    Renders a welcome message for the API, explaining how to use it.
    This handles GET requests to the base URL.
    """
    # Replace the placeholder YOUR_API_HOST with actual dynamically constructed host in HTML
    api_host = request.url_root # This will dynamically get the base URL (e.g., https://your-space.hf.space/)
    predict_endpoint = f"{api_host}predict"

    welcome_message = f"""
    <div style="font-family: Arial, sans-serif; text-align: center; margin-top: 50px; padding: 20px; background-color: #f9f9f9; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <h1 style="color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; margin-bottom: 20px;">
            Welcome to the Personality Prediction API!
        </h1>
        <p style="font-size: 1.1em; color: #555; line-height: 1.6;">
            This API predicts whether a person is an Introvert or Extrovert based on provided characteristics.
        </p>
        <p style="font-size: 1.1em; color: #555; line-height: 1.6;">
            To get a prediction, you need to send a <strong>POST request</strong> to the <strong><code>/predict</code></strong> endpoint.
        </p>
        <h2 style="color: #666; margin-top: 30px; border-bottom: 1px solid #ddd; padding-bottom: 5px;">How to use it:</h2>
        <div style="background-color: #fff; border: 1px solid #e0e0e0; padding: 20px; border-radius: 8px; display: inline-block; text-align: left; max-width: 600px; margin: 20px auto;">
            <p><strong>Endpoint:</strong> <code>{predict_endpoint}</code></p>
            <p><strong>Method:</strong> <code>POST</code></p>
            <p><strong>Content-Type:</strong> <code>application/json</code></p>
            <p><strong>Body (JSON example):</strong></p>
            <pre style="background-color: #eee; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: monospace; font-size: 0.9em; white-space: pre-wrap; word-wrap: break-word;"><code>{{
    "Time_spent_Alone": 7.0,
    "Stage_fear": "No",
    "Social_event_attendance": 2.0,
    "Going_outside": 1.0,
    "Drained_after_socializing": "Yes",
    "Friends_circle_size": 2.0,
    "Post_frequency": 1.0
}}</code></pre>
            <p style="margin-top: 15px; font-size: 0.9em; color: #777;">
                (Use the URL you see in your browser's address bar for the base host!)
            </p>
        </div>
        <p style="font-size: 0.9em; color: #777; margin-top: 20px;">
            You can use tools like <code>curl</code> (in terminal), Postman, or Python's <code>requests</code> library to send the POST request.
        </p>
    </div>
    """
    return render_template_string(welcome_message)

# --- Existing: Prediction Endpoint (POST request) ---
@app.route('/predict', methods=['POST'])
def predict():
    if loaded_model is None or loaded_le_personality is None:
        return jsonify({'error': 'Prediction service unavailable: Model not loaded on server.'}), 500

    try:
        request_data = request.get_json(force=True)
        print(f"Received prediction request with raw data: {request_data}")

        expected_feature_order = [
            'Time_spent_Alone',
            'Stage_fear',
            'Social_event_attendance',
            'Going_outside',
            'Drained_after_socializing',
            'Friends_circle_size',
            'Post_frequency'
        ]

        input_features_dict = {feature: request_data.get(feature) for feature in expected_feature_order}
        input_df = pd.DataFrame([input_features_dict])

        for col in ['Stage_fear', 'Drained_after_socializing']:
            if col in input_df.columns and input_df[col].iloc[0] is not None:
                input_df[col] = input_df[col].astype(str).apply(lambda x: 1 if x.lower() == 'yes' else 0)
            else:
                input_df[col] = 0

        for col in ['Time_spent_Alone', 'Social_event_attendance', 'Going_outside', 'Friends_circle_size', 'Post_frequency']:
            if col in input_df.columns:
                input_df[col] = pd.to_numeric(input_df[col], errors='coerce')
            else:
                input_df[col] = None

        input_df = input_df[expected_feature_order]

        prediction_encoded = loaded_model.predict(input_df)
        prediction_label = loaded_le_personality.inverse_transform(prediction_encoded)[0]

        return jsonify({'prediction': prediction_label})

    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({'error': f'An internal server error occurred during prediction: {str(e)}'}), 500

# --- Flask App Execution for Docker/Hugging Face Spaces ---
if __name__ == '__main__':
    # Hugging Face Spaces (and most cloud platforms) provide the port via an environment variable
    port = int(os.environ.get('PORT', 5000)) # Default to 5000 if PORT env var is not set
    print(f"Flask app starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False) # debug=False for production deployment
