#!/usr/bin/env python3

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import chi2_contingency, f_oneway, kruskal
import os
from pathlib import Path

# Set up paths
RESULTS_DIR = Path("results")
CONFUSION_DIR = RESULTS_DIR / "confusion_matrices"
OUTPUT_DIR = Path("results/statistical_analysis")

# Create output directory
OUTPUT_DIR.mkdir(exist_ok=True)

def load_performance_data():
    metrics_file = RESULTS_DIR / "performance_metrics.csv"
    df = pd.read_csv(metrics_file)
    return df

def load_confusion_matrices():
    confusion_matrices = {}
    models = ['svm', 'sgd', 'random_forest', 'hist_gradient_boosting_pca', 'cnn']
    
    for model in models:
        matrix_file = CONFUSION_DIR / f"{model}.csv"
        if matrix_file.exists():
            matrix = pd.read_csv(matrix_file, header=None).values
            confusion_matrices[model] = matrix
    
    return confusion_matrices

def calculate_detailed_metrics(confusion_matrices):
    detailed_metrics = []
    class_names = ['Word', 'Google', 'Python', 'LibreOffice', 'Browser']
    
    for model_name, matrix in confusion_matrices.items():
        class_metrics = {}
        
        for i, class_name in enumerate(class_names):
            tp = matrix[i, i]
            fp = matrix[:, i].sum() - tp
            fn = matrix[i, :].sum() - tp
            tn = matrix.sum() - tp - fp - fn
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
            
            class_metrics[class_name] = {
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'specificity': specificity,
                'tp': tp,
                'fp': fp,
                'fn': fn,
                'tn': tn
            }
        
        detailed_metrics.append({
            'model': model_name,
            'class_metrics': class_metrics,
            'total_samples': matrix.sum()
        })
    
    return detailed_metrics

def perform_statistical_tests(performance_df):
    accuracy = performance_df['accuracy'].values
    precision = performance_df['precision_macro'].values
    recall = performance_df['recall_macro'].values
    f1 = performance_df['f1_macro'].values
    
    results = {}
    
    print("=== ONE-WAY ANOVA TESTS ===")
    metrics = ['accuracy', 'precision', 'recall', 'f1']
    metric_values = [accuracy, precision, recall, f1]
    
    for metric_name, metric_data in zip(metrics, metric_values):
        f_stat, p_value = f_oneway(*[[val] for val in metric_data])
        results[f'{metric_name}_anova'] = {'f_stat': f_stat, 'p_value': p_value}
        
        print(f"{metric_name.upper()}:")
        print(f"  F-statistic: {f_stat:.6f}")
        print(f"  p-value: {p_value:.6f}")
        print(f"  Significant difference: {'Yes' if p_value < 0.05 else 'No'}")
        print()
    
    print("=== KRUSKAL-WALLIS TESTS (Non-parametric) ===")
    for metric_name, metric_data in zip(metrics, metric_values):
        h_stat, p_value = kruskal(*[[val] for val in metric_data])
        results[f'{metric_name}_kruskal'] = {'h_stat': h_stat, 'p_value': p_value}
        
        print(f"{metric_name.upper()}:")
        print(f"  H-statistic: {h_stat:.6f}")
        print(f"  p-value: {p_value:.6f}")
        print(f"  Significant difference: {'Yes' if p_value < 0.05 else 'No'}")
        print()
    
    print("=== PAIRWISE T-TESTS ===")
    models = performance_df['model'].values
    
    pairwise_results = {}
    for i in range(len(models)):
        for j in range(i+1, len(models)):
            model1, model2 = models[i], models[j]
            
            acc1, acc2 = accuracy[i], accuracy[j]
            t_stat, p_value = stats.ttest_ind([acc1], [acc2])
            
            pairwise_results[f"{model1}_vs_{model2}"] = {
                'accuracy_diff': acc1 - acc2,
                't_stat': t_stat,
                'p_value': p_value,
                'significant': p_value < 0.05
            }
            
            print(f"{model1} vs {model2}:")
            print(f"  Accuracy difference: {acc1 - acc2:.6f}")
            print(f"  t-statistic: {t_stat:.6f}")
            print(f"  p-value: {p_value:.6f}")
            print(f"  Significant difference: {'Yes' if p_value < 0.05 else 'No'}")
            print()
    
    return results, pairwise_results

def analyze_class_separability(confusion_matrices):
    print("=== CLASS SEPARABILITY ANALYSIS ===")
    
    class_names = ['Word', 'Google', 'Python', 'LibreOffice', 'Browser']
    separability_analysis = {}
    
    for model_name, matrix in confusion_matrices.items():
        print(f"\n{model_name.upper()}:")
        
        class_accuracies = []
        for i, class_name in enumerate(class_names):
            correct = matrix[i, i]
            total = matrix[i, :].sum()
            accuracy = correct / total if total > 0 else 0
            class_accuracies.append(accuracy)
            
            print(f"  {class_name}: {accuracy:.4f} ({correct}/{total})")
        
        confusion_patterns = {}
        for i, true_class in enumerate(class_names):
            for j, pred_class in enumerate(class_names):
                if i != j and matrix[i, j] > 0:
                    confusion_patterns[f"{true_class}_as_{pred_class}"] = matrix[i, j]
        
        separability_analysis[model_name] = {
            'class_accuracies': dict(zip(class_names, class_accuracies)),
            'confusion_patterns': confusion_patterns,
            'overall_accuracy': matrix.trace() / matrix.sum()
        }
    
    return separability_analysis

def main():
    print("Starting Statistical Analysis of Classifier Performance Differences...")
    
    performance_df = load_performance_data()
    confusion_matrices = load_confusion_matrices()
    
    detailed_metrics = calculate_detailed_metrics(confusion_matrices)
    statistical_results, pairwise_results = perform_statistical_tests(performance_df)
    separability_analysis = analyze_class_separability(confusion_matrices)
    
    print("\n" + "="*60)
    print("STATISTICAL ANALYSIS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()
