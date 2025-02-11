import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt

# Step 1: Load the Data
data = pd.read_csv('breakout_data.csv')

# Step 2: Preprocess the Data
# Drop the 'time' column as it's not useful for prediction
data = data.drop(columns=['time'])

# Convert categorical 'breakout_type' to numerical using one-hot encoding
data = pd.get_dummies(data, columns=['breakout_type'], drop_first=True)

# Define features (X) and target (y)
X = data.drop(columns=['size'])
y = data['size']

# Step 3: Split the Data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Step 4: Train the Model
model = RandomForestRegressor(random_state=42)
model.fit(X_train, y_train)

# Step 5: Evaluate the Model
y_pred = model.predict(X_test)

# Calculate evaluation metrics
mse = mean_squared_error(y_test, y_pred)
rmse = mse ** 0.5  # Root Mean Squared Error
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

# Print the metrics
print(f'Mean Squared Error (MSE): {mse}')
print(f'Root Mean Squared Error (RMSE): {rmse}')
print(f'Mean Absolute Error (MAE): {mae}')
print(f'R² Score (Coefficient of Determination): {r2}')


# Step 6: Make Predictions
# Example: Predict the size of a new candle
# new_data = pd.DataFrame({
#     'volume': [2441],
#     'Candle1Size': [5.4849999999999],
#     'Candle2Size': [1.900000000000091],
#     'Candle3Size': [1.5199999999999818],
#     'Candle4Size': [9.710000000000036],
#     'support_level': [1830.02],
#     'resistance_level': [1863.9],
#     'breakout_type_support': [1]  # Assuming 'support' is encoded as 1
# })

# predicted_size = model.predict(new_data)
# print(f'Predicted Size: {predicted_size[0]}')



plt.scatter(y_test, y_pred)
plt.xlabel('Actual Size')
plt.ylabel('Predicted Size')
plt.title('Actual vs Predicted Size')
plt.show()