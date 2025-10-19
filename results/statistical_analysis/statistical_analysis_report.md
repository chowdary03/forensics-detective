# Statistical Analysis of Classifier Performance Differences

## Summary Statistics

| Model | Accuracy | Precision | Recall | F1-Score |
|-------|----------|-----------|--------|----------|
| SVM | 0.9912 | 0.9912 | 0.9911 | 0.9911 |
| SGD | 0.9848 | 0.9848 | 0.9848 | 0.9848 |
| RandomForest | 0.9900 | 0.9901 | 0.9902 | 0.9901 |
| HistGradientBoosting+PCA | 0.9981 | 0.9981 | 0.9981 | 0.9981 |
| CNN | 0.9998 | 0.9998 | 0.9998 | 0.9998 |

## Statistical Tests

### One-Way ANOVA Tests

The ANOVA tests determine if there are statistically significant differences between classifiers.

**Accuracy:** F-statistic = nan, p-value = nan, Significant difference = No

**Precision:** F-statistic = nan, p-value = nan, Significant difference = No

**Recall:** F-statistic = nan, p-value = nan, Significant difference = No

**F1:** F-statistic = nan, p-value = nan, Significant difference = No

### Pairwise Comparisons

Pairwise t-tests comparing each classifier pair:

**SVM vs SGD:** Difference = 0.006386, p-value = nan, Significant = No

**SVM vs RandomForest:** Difference = 0.001127, p-value = nan, Significant = No

**SVM vs HistGradientBoosting+PCA:** Difference = -0.006950, p-value = nan, Significant = No

**SVM vs CNN:** Difference = -0.008640, p-value = nan, Significant = No

**SGD vs RandomForest:** Difference = -0.005259, p-value = nan, Significant = No

**SGD vs HistGradientBoosting+PCA:** Difference = -0.013336, p-value = nan, Significant = No

**SGD vs CNN:** Difference = -0.015026, p-value = nan, Significant = No

**RandomForest vs HistGradientBoosting+PCA:** Difference = -0.008077, p-value = nan, Significant = No

**RandomForest vs CNN:** Difference = -0.009767, p-value = nan, Significant = No

**HistGradientBoosting+PCA vs CNN:** Difference = -0.001690, p-value = nan, Significant = No

## Class Separability Analysis

### SVM

**Per-class accuracy:**

- Word: 0.9841

- Google: 0.9851

- Python: 1.0000

- LibreOffice: 0.9991

- Browser: 0.9870

**Main confusion patterns:**

- Word_as_Google: 4 misclassifications

- Word_as_Browser: 12 misclassifications

- Google_as_Word: 2 misclassifications

- Google_as_Browser: 14 misclassifications

- LibreOffice_as_Python: 1 misclassifications

- Browser_as_Word: 6 misclassifications

- Browser_as_Google: 8 misclassifications

**Overall accuracy:** 0.9912


### SGD

**Per-class accuracy:**

- Word: 0.9851

- Google: 0.9703

- Python: 1.0000

- LibreOffice: 0.9972

- Browser: 0.9713

**Main confusion patterns:**

- Word_as_Google: 1 misclassifications

- Word_as_Python: 8 misclassifications

- Word_as_Browser: 6 misclassifications

- Google_as_Word: 5 misclassifications

- Google_as_Python: 9 misclassifications

- Google_as_Browser: 18 misclassifications

- LibreOffice_as_Python: 1 misclassifications

- LibreOffice_as_Browser: 2 misclassifications

- Browser_as_Word: 13 misclassifications

- Browser_as_Google: 8 misclassifications

- Browser_as_Python: 10 misclassifications

**Overall accuracy:** 0.9848


### RANDOM_FOREST

**Per-class accuracy:**

- Word: 1.0000

- Google: 0.9675

- Python: 1.0000

- LibreOffice: 0.9981

- Browser: 0.9852

**Main confusion patterns:**

- Google_as_Word: 4 misclassifications

- Google_as_Browser: 31 misclassifications

- LibreOffice_as_Browser: 2 misclassifications

- Browser_as_Word: 8 misclassifications

- Browser_as_Google: 7 misclassifications

- Browser_as_LibreOffice: 1 misclassifications

**Overall accuracy:** 0.9900


### HIST_GRADIENT_BOOSTING_PCA

**Per-class accuracy:**

- Word: 1.0000

- Google: 0.9944

- Python: 1.0000

- LibreOffice: 1.0000

- Browser: 0.9963

**Main confusion patterns:**

- Google_as_Word: 1 misclassifications

- Google_as_Browser: 5 misclassifications

- Browser_as_Word: 1 misclassifications

- Browser_as_Google: 3 misclassifications

**Overall accuracy:** 0.9981


### CNN

**Per-class accuracy:**

- Word: 1.0000

- Google: 1.0000

- Python: 1.0000

- LibreOffice: 1.0000

- Browser: 0.9991

**Main confusion patterns:**

- Browser_as_Google: 1 misclassifications

**Overall accuracy:** 0.9998


## Performance Ranking

### Ranked by Accuracy:

1. **CNN**: 0.9998

2. **HistGradientBoosting+PCA**: 0.9981

3. **SVM**: 0.9912

4. **RandomForest**: 0.9900

5. **SGD**: 0.9848

### Effect Size Analysis

The difference between best (CNN) and worst (SGD) performing classifiers is 0.0150 (1.50 percentage points).

This represents a **large practical difference** in performance.

## Conclusions

1. **Best Performing Classifier**: CNN with 0.9998 accuracy

2. **Statistical Significance**: No statistically significant differences detected between classifiers (p ≥ 0.05)

3. **Practical Significance**: Large practical differences exist between classifiers, making model selection important for deployment
