import seaborn as sns
import matplotlib.pyplot as plt


def plot_hist(rss_data, vms_data, sav_loc, exam_name):

    # Create a figure with subplots
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    # Plot histograms side by side
    sns.histplot(rss_data, ax=axes[0], color='blue', alpha=0.5, label='RSS')
    sns.histplot(vms_data, ax=axes[1], color='orange', alpha=0.5, label='VMS')

    # Add labels and title
    axes[0].set_xlabel('Value')
    axes[0].set_ylabel('Frequency')
    axes[0].set_title(f'{exam_name} - RSS')
    axes[0].legend()

    axes[1].set_xlabel('Value')
    axes[1].set_ylabel('Frequency')
    axes[1].set_title(f'{exam_name} - VMS')
    axes[1].legend()

    # Adjust layout
    plt.tight_layout()

    plt.savefig(f"{sav_loc}_histogram.png")