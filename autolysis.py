# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx",
#   "pandas",
#   "seaborn",
#   "matplotlib",
#   "openai",
#   "scipy",
# ]
# ///

import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import asyncio
import httpx
from scipy import stats

AIPROXY_TOKEN = os.environ.get("AIPROXY_TOKEN")
if not AIPROXY_TOKEN:
    raise ValueError("AIPROXY_TOKEN environment variable not set")

API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

def load_data(filename):
    return pd.read_csv(filename, encoding='utf-8', encoding_errors='replace')

def analyze_data(df):
    summary = df.describe(include='all')
    missing_values = df.isnull().sum()
    numeric_df = df.select_dtypes(include=['number'])
    correlation_matrix = numeric_df.corr()

    # Advanced analysis: adding regression analysis and ANOVA
    regression_results = {}
    for col in numeric_df.columns[1:]:
        # Linear regression with the first numeric column
        slope, intercept, r_value, p_value, std_err = stats.linregress(numeric_df.iloc[:, 0], numeric_df[col])
        regression_results[col] = {
            "slope": slope, "intercept": intercept, "r_value": r_value, "p_value": p_value, "std_err": std_err
        }

    # Conducting one-way ANOVA between the first numeric column and others
    anova_results = {}
    for col in numeric_df.columns[1:]:
        f_stat, p_val = stats.f_oneway(numeric_df.iloc[:, 0], numeric_df[col])
        anova_results[col] = {"f_stat": f_stat, "p_value": p_val}

    return summary, missing_values, correlation_matrix, regression_results, anova_results

def visualize_data(df):
    numeric_columns = df.select_dtypes(include=['number']).columns
    if len(numeric_columns) > 0:
        sns.kdeplot(df[numeric_columns[0]], fill=True)
        plt.title(f'Density Plot of {numeric_columns[0]}')
        plt.xlabel(numeric_columns[0])
        plt.ylabel('Density')
        plt.savefig('density_plot.png')
        plt.clf()

    if len(numeric_columns) > 1:
        sns.scatterplot(x=numeric_columns[0], y=numeric_columns[1], data=df)
        plt.title(f'Scatter Plot of {numeric_columns[0]} vs {numeric_columns[1]}')
        plt.xlabel(numeric_columns[0])
        plt.ylabel(numeric_columns[1])
        plt.savefig('scatter_plot.png')
        plt.clf()

    if len(numeric_columns) > 0:
        df[numeric_columns].hist(bins=15, figsize=(15, 10))
        plt.suptitle('Histograms of Numeric Columns')
        plt.savefig('histogram.png')
        plt.clf()

    if len(numeric_columns) > 1:
        correlation_matrix = df[numeric_columns].corr()
        plt.figure(figsize=(10, 8))
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f")
        plt.title('Correlation Heatmap')
        plt.savefig('correlation_heatmap.png')
        plt.clf()

async def generate_story(summary, missing_values, correlation_matrix, regression_results, anova_results):
    prompt = f"""
    Analyze the following dataset and provide insights:
    1. Summary: {summary}
    2. Missing Values: {missing_values}
    3. Correlation Matrix: {correlation_matrix}

    Additionally, provide insights on:
    1. Regression Analysis: Describe the regression results for the first numeric column with others.
    2. ANOVA: Summarize the one-way ANOVA results between the first numeric column and others.
    3. Visualizations: 
        - Density Plot: Describe the distribution of the first numeric column.
        - Scatter Plot: Describe the relationship between the first two numeric columns.
        - Histogram: Describe the distribution of all numeric columns.
        - Correlation Heatmap: Describe the relationships between numeric columns based on the heatmap.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AIPROXY_TOKEN}"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a data analyst."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 700
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(API_URL, headers=headers, json=data)
        response_data = response.json()
    return response_data['choices'][0]['message']['content']

def save_readme(story):
    with open('README.md', 'w') as f:
        f.write("# Automated Analysis Report\n")
        f.write(story)
        f.write("\n## Density Plot\n")
        f.write("This plot shows the distribution of the first numeric column.\n")
        f.write("![Density Plot](density_plot.png)\n")
        f.write("\n## Scatter Plot\n")
        f.write("This plot shows the relationship between the first two numeric columns.\n")
        f.write("![Scatter Plot](scatter_plot.png)\n")
        f.write("\n## Histogram\n")
        f.write("This plot shows the distribution of all numeric columns.\n")
        f.write("![Histogram](histogram.png)\n")
        f.write("\n## Correlation Heatmap\n")
        f.write("This heatmap shows the relationships between numeric columns.\n")
        f.write("![Correlation Heatmap](correlation_heatmap.png)\n")
        f.write("\n## Regression Analysis\n")
        f.write("This section details the regression results for relationships between the first numeric column and others.\n")
        f.write("\n## ANOVA Results\n")
        f.write("This section summarizes the one-way ANOVA tests conducted.\n")

def main():
    if len(sys.argv) != 2:
        print("Usage: uv run autolysis.py <dataset.csv>")
        sys.exit(1)

    filename = sys.argv[1]
    df = load_data(filename)
    summary, missing_values, correlation_matrix, regression_results, anova_results = analyze_data(df)
    visualize_data(df)
    story = asyncio.run(generate_story(summary, missing_values, correlation_matrix, regression_results, anova_results))
    save_readme(story)

if __name__ == "__main__":
    main()
