#!/usr/bin/env python3
"""
5-Class PDF Provenance Classifiers

Trains SVM, SGD, and a CNN to classify PDFs by generation method:
- Microsoft Word (label 0)
- Google Docs (label 1)
- Python/ReportLab (label 2)
- LibreOffice (label 3)
- Browser/Chromium Print-to-PDF (label 4)

Implementation requirements satisfied:
- Integration: Adds SVM, SGD, CNN to the existing training workflow
- Hyperparameter Tuning: Grid/Randomized search with k-fold CV
- Consistent Evaluation: Same split/metrics as existing classifiers
- Documentation: Inline comments explain key parameters and choices
- Cross-Validation: Uses cv=5 during model selection
- Metrics: Accuracy, precision, recall, F1 (macro) and detailed reports
"""

import os
import time
import pickle
import json
import numpy as np
import random
from typing import Tuple, Dict, Any

from PIL import Image
from sklearn.model_selection import train_test_split, GridSearchCV, RandomizedSearchCV
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix,
)
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.linear_model import SGDClassifier
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.utils.class_weight import compute_class_weight

import tensorflow as tf
from keras.callbacks import EarlyStopping, ReduceLROnPlateau
from keras import Sequential
from keras.layers import (
    Input, Conv2D, MaxPooling2D, Dropout, Dense, BatchNormalization,
    RandomFlip, RandomRotation, RandomZoom, RandomTranslation, RandomContrast,
    SeparableConv2D, GlobalAveragePooling2D
)
from keras.optimizers import Adam
from keras.regularizers import l2
from keras.losses import SparseCategoricalCrossentropy

def load_4class_dataset(
    word_dir: str = 'word_pdfs_png',
    google_dir: str = 'google_docs_pdfs_png',
    python_dir: str = 'python_pdfs_png',
    libreoffice_dir: str = 'lo_pdfs_png',
    browser_dir: str = 'fifth_pdfs_png',
    *,
    max_samples_per_class: int = None,
    target_size: Tuple[int, int] = (200, 200),
) -> Tuple[np.ndarray, np.ndarray, Tuple[int, int]]:
    """
    Load 4-class binary image dataset.

    Returns:
        X (N, H*W): Flattened grayscale images for classical models
        y (N,): Class labels (0..3)
        hw (H, W): Original height/width used for CNN reshaping
    """
    def _load_dir(img_dir: str, label: int) -> Tuple[np.ndarray, np.ndarray]:
        files = [f for f in os.listdir(img_dir) if f.endswith('.png')]
        if max_samples_per_class:
            files = files[:max_samples_per_class]
        images = []
        labels = []
        for i, filename in enumerate(files):
            img_path = os.path.join(img_dir, filename)
            img = Image.open(img_path).convert('L')  # ensure grayscale
            img = img.resize(target_size, Image.LANCZOS)
            images.append(np.array(img).flatten())
            labels.append(label)
        return np.array(images), np.array(labels)

    X_word, y_word = _load_dir(word_dir, 0)
    X_google, y_google = _load_dir(google_dir, 1)
    X_python, y_python = _load_dir(python_dir, 2)
    X_lo, y_lo = _load_dir(libreoffice_dir, 3)
    X_browser, y_browser = _load_dir(browser_dir, 4)

    parts_X = [X_word, X_google, X_python, X_lo, X_browser]
    parts_y = [y_word, y_google, y_python, y_lo, y_browser]
    parts_X = [p for p in parts_X if p.size]
    parts_y = [p for p in parts_y if p.size]
    X = np.concatenate(parts_X, axis=0)
    y = np.concatenate(parts_y, axis=0)

    print(f"Dataset loaded: {X.shape[0]} samples, {X.shape[1]} features per sample")
    print(
        "Class distribution: "
        f"Word={np.sum(y==0)}, Google={np.sum(y==1)}, Python={np.sum(y==2)}, LibreOffice={np.sum(y==3)}, Browser={np.sum(y==4)}"
    )
    return X, y, target_size


def tune_and_train_svm(X_train: np.ndarray, y_train: np.ndarray) -> GridSearchCV:
    """
    Grid search SVM hyperparameters with 5-fold CV; optimize macro F1.
    """
    param_grid = {
        'C': [0.1, 1.0, 10.0],
        'gamma': ['scale', 'auto'],
        'kernel': ['rbf', 'linear'],
    }
    svm = SVC(random_state=42)
    search = GridSearchCV(
        svm,
        param_grid,
        scoring='f1_macro',
        cv=5,
        n_jobs=-1,
        verbose=1,
    )
    search.fit(X_train, y_train)
    return search


def tune_and_train_sgd(X_train: np.ndarray, y_train: np.ndarray) -> RandomizedSearchCV:
    """
    Randomized search for SGD hyperparameters with 5-fold CV; optimize macro F1.
    """
    param_dist = {
        'loss': ['hinge', 'log_loss', 'modified_huber'],
        'alpha': [1e-4, 1e-3, 1e-2],
        'penalty': ['l2', 'l1', 'elasticnet'],
        'max_iter': [1000, 2000],
        'tol': [1e-3, 1e-4],
    }
    sgd = SGDClassifier(random_state=42)
    search = RandomizedSearchCV(
        sgd,
        param_distributions=param_dist,
        n_iter=12,
        scoring='f1_macro',
        cv=5,
        n_jobs=-1,
        verbose=1,
        random_state=42,
    )
    search.fit(X_train, y_train)
    return search


def build_cnn(
    input_shape: Tuple[int, int, int],
    num_classes: int = 4,
    *,
    base_filters: int = 32,
    weight_decay: float = 1e-4,
    dropout_dense: float = 0.4,
    learning_rate: float = 1e-3,
    use_highpass: bool = True,
    label_smoothing: float = 0.05,
):
    """
    Compact separable-conv CNN with optional fixed high-pass residual prefilter,
    lightweight augmentations, L2 regularization, label smoothing, and GAP head.
    """
    layers = [
        Input(shape=input_shape),
        # Light augmentations appropriate for document forensics
        RandomFlip("horizontal"),
        RandomRotation(0.02),
        RandomTranslation(0.02, 0.02),
        RandomZoom(0.05, 0.05),
        RandomContrast(0.1),
    ]

    if use_highpass:
        # 5x5 high-pass residual kernel (sum ~ 0) to emphasize subtle rendering noise
        hp_kernel = np.array([
            [0, 0, -1, 0, 0],
            [0, -1, 2, -1, 0],
            [-1, 2, 4, 2, -1],
            [0, -1, 2, -1, 0],
            [0, 0, -1, 0, 0],
        ], dtype=np.float32)
        hp_kernel = hp_kernel / max(1.0, float(np.sum(np.abs(hp_kernel))))
        hp_kernel = hp_kernel.reshape((5, 5, 1, 1))
        layers.extend([
            Conv2D(
                1, (5, 5), padding='same', use_bias=False,
                kernel_initializer=tf.constant_initializer(hp_kernel),
                trainable=False,
            ),
            BatchNormalization(),
        ])

    # SeparableConv blocks
    def sep_block(filters: int, pool: bool, dropout_rate: float):
        block = [
            SeparableConv2D(filters, (3, 3), padding='same', activation='relu',
                            depthwise_regularizer=l2(weight_decay), pointwise_regularizer=l2(weight_decay)),
            BatchNormalization(),
            SeparableConv2D(filters, (3, 3), padding='same', activation='relu',
                            depthwise_regularizer=l2(weight_decay), pointwise_regularizer=l2(weight_decay)),
            BatchNormalization(),
        ]
        if pool:
            block.append(MaxPooling2D((2, 2)))
        block.append(Dropout(dropout_rate))
        return block

    layers.extend(sep_block(base_filters, pool=True, dropout_rate=0.15))
    layers.extend(sep_block(base_filters * 2, pool=True, dropout_rate=0.25))
    layers.extend([
        SeparableConv2D(base_filters * 3, (3, 3), padding='same', activation='relu',
                        depthwise_regularizer=l2(weight_decay), pointwise_regularizer=l2(weight_decay)),
        BatchNormalization(),
        MaxPooling2D((2, 2)),
        Dropout(0.35),
    ])

    layers.extend([
        GlobalAveragePooling2D(),
        Dense(128, activation='relu', kernel_regularizer=l2(weight_decay)),
        Dropout(dropout_dense),
        Dense(num_classes, activation='softmax'),
    ])

    model = Sequential(layers)
    model.compile(
        optimizer=Adam(learning_rate=learning_rate),
        loss=SparseCategoricalCrossentropy(label_smoothing=label_smoothing),
        metrics=['accuracy']
    )
    return model


def train_and_select_cnn(
    X_tr_img: np.ndarray,
    y_tr: np.ndarray,
    input_hw: Tuple[int, int],
    class_weights: Dict[int, float],
) -> Tuple[Any, Dict[str, Any]]:
    """
    Run a small hyperparameter search over compact CNN variants and return the best model.
    """
    H, W = input_hw
    input_shape = (H, W, 1)
    configs = [
        {"base_filters": 32, "weight_decay": 1e-4, "dropout_dense": 0.4, "learning_rate": 1e-3},
        {"base_filters": 48, "weight_decay": 5e-4, "dropout_dense": 0.45, "learning_rate": 7e-4},
        {"base_filters": 64, "weight_decay": 1e-4, "dropout_dense": 0.5, "learning_rate": 5e-4},
    ]

    best_val_acc = -1.0
    best_model = None
    best_cfg = None

    es = EarlyStopping(monitor='val_accuracy', patience=6, restore_best_weights=True)
    rlrop = ReduceLROnPlateau(monitor='val_accuracy', factor=0.5, patience=2, min_lr=1e-5)

    for cfg in configs:
        model = build_cnn(
            input_shape,
            num_classes=4,
            base_filters=cfg["base_filters"],
            weight_decay=cfg["weight_decay"],
            dropout_dense=cfg["dropout_dense"],
            learning_rate=cfg["learning_rate"],
            use_highpass=True,
        )
        history = model.fit(
            X_tr_img, y_tr,
            validation_split=0.12,
            epochs=60,
            batch_size=128,
            callbacks=[es, rlrop],
            verbose=0,
            class_weight=class_weights,
        )
        val_acc = max(history.history.get('val_accuracy', [0.0]))
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_model = model
            best_cfg = cfg

    return best_model, {"val_accuracy": float(best_val_acc), "config": best_cfg}


def evaluate_classifier(name: str, y_true: np.ndarray, y_pred: np.ndarray) -> None:
    acc = accuracy_score(y_true, y_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='macro', zero_division=0)
    print(f"\n{name} Results")
    print(f"Accuracy: {acc:.4f} | Precision (macro): {prec:.4f} | Recall (macro): {rec:.4f} | F1 (macro): {f1:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, target_names=['Word','Google','Python','LibreOffice','Browser']))
    print("Confusion Matrix:")
    print(confusion_matrix(y_true, y_pred))


def main() -> None:
    print("PDF Provenance Detection - 5-Class Classification")
    print("=" * 60)
    print("Classes: Word (0), Google Docs (1), Python/ReportLab (2), LibreOffice (3), Browser (4)")
    print("=" * 60)

    # Load combined 4-class dataset
    X, y, hw = load_4class_dataset(max_samples_per_class=None, target_size=(200, 200))

    # Use a single index-based split, so CNN can use raw pixels and SVM/SGD scaled features
    idx = np.arange(len(y))
    tr_idx, te_idx = train_test_split(idx, test_size=0.2, random_state=42, stratify=y)

    # Classical models scaler
    scaler = StandardScaler()
    X_tr = scaler.fit_transform(X[tr_idx])
    X_te = scaler.transform(X[te_idx])
    y_tr = y[tr_idx]
    y_te = y[te_idx]

    # 1) SVM with grid search and 5-fold CV
    print("\n=== Tuning SVM (GridSearchCV, cv=5, scoring=f1_macro) ===")
    t0 = time.time()
    svm_search = tune_and_train_svm(X_tr, y_tr)
    print(f"Best SVM params: {svm_search.best_params_}")
    print(f"SVM tuning time: {time.time()-t0:.2f}s")
    y_pred_svm = svm_search.best_estimator_.predict(X_te)
    evaluate_classifier("SVM", y_te, y_pred_svm)

    # 2) SGD with randomized search and 5-fold CV
    print("\n=== Tuning SGD (RandomizedSearchCV, cv=5, scoring=f1_macro) ===")
    t0 = time.time()
    sgd_search = tune_and_train_sgd(X_tr, y_tr)
    print(f"Best SGD params: {sgd_search.best_params_}")
    print(f"SGD tuning time: {time.time()-t0:.2f}s")
    y_pred_sgd = sgd_search.best_estimator_.predict(X_te)
    evaluate_classifier("SGD", y_te, y_pred_sgd)

    # 3) RandomForest with grid search
    print("\n=== Tuning RandomForest (GridSearchCV, cv=5, scoring=f1_macro) ===")
    rf_params = { 'n_estimators': [200, 400], 'max_depth': [None, 20, 40] }
    rf = RandomForestClassifier(random_state=42, n_jobs=-1)
    rf_search = GridSearchCV(rf, rf_params, scoring='f1_macro', cv=5, n_jobs=-1, verbose=1)
    rf_search.fit(X_tr, y_tr)
    print(f"Best RF params: {rf_search.best_params_}")
    y_pred_rf = rf_search.best_estimator_.predict(X_te)
    evaluate_classifier("RandomForest", y_te, y_pred_rf)

    # 4) Fast HistGradientBoosting with PCA and early stopping
    print("\n=== Tuning HistGradientBoosting + PCA (RandomizedSearchCV, cv=3, scoring=f1_macro) ===")
    hgb_pipe = Pipeline([
        ('pca', PCA(n_components=256, random_state=42)),
        ('hgb', HistGradientBoostingClassifier(
            early_stopping=True,
            validation_fraction=0.1,
            random_state=42,
        )),
    ])
    hgb_dist = {
        'pca__n_components': [128, 256],
        'hgb__learning_rate': [0.05, 0.1],
        'hgb__max_leaf_nodes': [15, 31],
        'hgb__max_iter': [80, 120, 160],
        'hgb__l2_regularization': [0.0, 1e-4, 1e-3],
        'hgb__min_samples_leaf': [20, 50],
    }
    hgb_search = RandomizedSearchCV(
        hgb_pipe,
        hgb_dist,
        n_iter=6,
        scoring='f1_macro',
        cv=3,
        n_jobs=-1,
        random_state=42,
        verbose=1,
    )
    hgb_search.fit(X_tr, y_tr)
    print(f"Best HGB params: {hgb_search.best_params_}")
    y_pred_hgb = hgb_search.best_estimator_.predict(X_te)
    evaluate_classifier("HistGradientBoosting+PCA", y_te, y_pred_hgb)

    # 5) CNN: compact forensic-focused model with small hyperparam search
    print("\n=== Training CNN (separable + high-pass, with tuning) ===")
    # Reproducibility
    np.random.seed(42)
    random.seed(42)
    try:
        tf.random.set_seed(42)
    except Exception:
        pass

    H, W = hw
    X_tr_img = (X[tr_idx].reshape((-1, H, W, 1)) / 255.0).astype(np.float32)
    X_te_img = (X[te_idx].reshape((-1, H, W, 1)) / 255.0).astype(np.float32)

    # Class weights to mitigate imbalance
    classes = np.unique(y_tr)
    weights = compute_class_weight(class_weight='balanced', classes=classes, y=y_tr)
    class_weights = {int(c): float(w) for c, w in zip(classes, weights)}

    t0 = time.time()
    cnn, cnn_meta = train_and_select_cnn(X_tr_img, y_tr, hw, class_weights)
    print(f"Best CNN config: {cnn_meta['config']} | Best val_accuracy: {cnn_meta['val_accuracy']:.4f}")
    print(f"CNN tuning+train time: {time.time()-t0:.2f}s")
    y_pred_cnn = np.argmax(cnn.predict(X_te_img, verbose=0), axis=1)
    evaluate_classifier("CNN", y_te, y_pred_cnn)

    # Save models, scaler, and confusion matrices
    print("\nSaving trained models and results...")
    with open('svm_5class_model.pkl', 'wb') as f:
        pickle.dump(svm_search.best_estimator_, f)
    with open('sgd_5class_model.pkl', 'wb') as f:
        pickle.dump(sgd_search.best_estimator_, f)
    # Save CNN and its best config
    try:
        cnn.save('cnn_5class_model.h5')
    except Exception as e:
        print(f"Warning: Could not save CNN model as .h5: {e}")
    try:
        with open('cnn_5class_best_config.json', 'w') as f:
            json.dump(cnn_meta, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save CNN config json: {e}")
    with open('scaler_5class.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    try:
        cnn.save('cnn_5class_model.keras')
    except Exception:
        pass
    print("Models saved.")


if __name__ == "__main__":
    main()
