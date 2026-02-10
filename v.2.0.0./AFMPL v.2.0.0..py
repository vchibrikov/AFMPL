"""
AFMPL v.2.0.0.
----------------------------------------
A GUI-based tool for analyzing AFM images.
Features:
- Loads Bruker AFM files using pySPM.
- Preprocesses images (line/plane correction, scar removal).
- Segments fibers based on height thresholding.
- Skeletonizes fibers and separates backbones from branches.
- Exports analysis results to Excel and visualizations to PNG.

Author: Vadym Chibrikov
License: MIT
"""

import os
import gc
import pandas as pd
import numpy as np
import networkx as nx
import pySPM
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Slider, Button, TextBox
from matplotlib.colors import ListedColormap
import xlsxwriter

from skimage.morphology import skeletonize, remove_small_objects, binary_erosion, disk
from skimage.segmentation import clear_border
from skimage.measure import label 
from skimage.transform import rescale

# --- CONFIGURATION ---
# Users should update these paths before running
INPUT_FOLDER = r'path/to/your/input/folder'
OUTPUT_FOLDER = r'path/to/your/output/folder'

# --- DEFAULT SETTINGS ---
DEFAULT_MIN_H = 0.2       # Min height threshold for auto-tune range (nm)
DEFAULT_MAX_H = 3.0       # Max height threshold for auto-tune range (nm)
DEFAULT_STEP = 0.05       # Step size for auto-tune scan (nm)
DEFAULT_PLAT_RANGE = 0.10 # Range (+/- nm) to check for plateau stability
DEFAULT_PLAT_TOL = 5.0    # Max allowed tolerance (%) for stability
AUTO_TUNE_DOWNSAMPLE = 0.5 # Scale factor for auto-tune (0.5 = 4x faster)

# --- VISUALIZATION COLORS ---
COLOR_BLOB = 'darkred'       
COLOR_BACKBONE = 'darkgreen' 
COLOR_BRANCH = 'darkblue'    
COLOR_BG_APP = '#f0f0f0'     

class HeightFilterTool:
    def __init__(self, input_folder, output_folder):
        self.input_folder = input_folder
        self.output_folder = output_folder
        
        if not os.path.exists(self.input_folder):
            print(f"Error: Input folder not found: {self.input_folder}")
            return
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            
        self.files = [f for f in os.listdir(self.input_folder) if not f.startswith('.')]
        self.files.sort()
        self.current_idx = 0
        
        # Parameters dictionary
        self.params = {
            'min_size': 10,
            'auto_min': DEFAULT_MIN_H,
            'auto_max': DEFAULT_MAX_H,
            'auto_step': DEFAULT_STEP,
            'plat_range': DEFAULT_PLAT_RANGE,
            'plat_tol': DEFAULT_PLAT_TOL
        }
        
        self.valid_chains = [] 
        self.current_mask = None
        self.plot_lines = [] 
        self.bg_median = 0.0 
        
        print("Starting AFM Height Filter Tool...")
        self.load_next_image()

    def load_next_image(self):
        """Loads the current AFM image file and applies preprocessing."""
        # Bounds check
        if self.current_idx < 0: self.current_idx = 0
        if self.current_idx >= len(self.files):
            print("All files processed!")
            plt.close('all')
            return

        # Clear memory
        self.valid_chains = [] 
        self.plot_lines = []
        self.current_mask = None
        gc.collect() 

        self.current_filename = self.files[self.current_idx]
        file_path = os.path.join(self.input_folder, self.current_filename)
        
        try:
            # Load AFM data using pySPM
            image = pySPM.Bruker(file_path)
            height = image.get_channel("Height Sensor")
            
            # Preprocessing Pipeline
            top = height.correct_lines(inline=False)
            top = top.correct_plane(inline=False)
            top = top.filter_scars_removal(.7, inline=False)
            top = top.correct_plane(inline=False)
            top = top.corr_fit2d(inline=False).offset([[10, 0, 10, 255]]).filter_scars_removal()
            
            # Initial mask for plane correction refinement
            mask0 = top.get_bin_threshold(.1, high=False)
            mask1 = binary_erosion(mask0, disk(3))
            top = top.corr_fit2d(mask=mask1, inline=False).offset([[10, 0, 10, 255]]).filter_scars_removal().correct_plane().correct_lines().zero_min()
            
            self.height_grid = top.pixels
            
            self.setup_gui()
            self.update_status(f"Loaded: {self.current_filename} ({self.current_idx + 1}/{len(self.files)})")
            
            # Fast initial view
            self.update_view_only()

        except Exception as e:
            print(f"Failed to load {self.current_filename}: {e}")
            self.current_idx += 1
            self.load_next_image()

    def update_status(self, text, color='black'):
        """Updates the status text on the GUI."""
        if hasattr(self, 'status_text'):
            self.status_text.set_text(text)
            self.status_text.set_color(color)
            self.fig.canvas.draw_idle()
        print(f"[Status] {text}") 

    def setup_gui(self):
        """Initializes the Matplotlib GUI layout."""
        plt.close('all')
        self.fig = plt.figure(figsize=(16, 10), facecolor=COLOR_BG_APP)
        self.fig.canvas.manager.set_window_title(f"AFM Analysis - {self.current_filename}")
        
        gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1], hspace=0.3)
        
        # --- IMAGES PANEL ---
        gs_images = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=gs[0], wspace=0.1)
        self.ax_raw = self.fig.add_subplot(gs_images[0])
        self.ax_skel = self.fig.add_subplot(gs_images[1])
        
        # --- CONTROLS PANEL ---
        row_btn_y = 0.03
        row_txt_y = 0.10
        row_sld_y = 0.18
        
        # 1. SLIDERS
        ax_thresh = plt.axes([0.15, row_sld_y, 0.30, 0.03], facecolor='white')
        ax_size   = plt.axes([0.55, row_sld_y, 0.30, 0.03], facecolor='white')
        
        h_min, h_max = np.min(self.height_grid), np.max(self.height_grid)
        self.s_thresh = Slider(ax_thresh, 'Height Threshold', h_min, h_max, valinit=0.5, color=COLOR_BLOB) 
        self.s_size = Slider(ax_size, 'Min Size (px)', 1, 100, valinit=self.params['min_size'], valstep=1, color='gray')

        # Connect sliders to fast view update
        self.s_thresh.on_changed(self.update_view_only)
        self.s_size.on_changed(self.update_view_only)

        # 2. PARAMETERS (Text Boxes)
        self.fig.text(0.05, row_txt_y + 0.02, "Auto-Tune Range:", fontsize=9, fontweight='bold')
        ax_min = plt.axes([0.13, row_txt_y, 0.05, 0.04])
        ax_max = plt.axes([0.20, row_txt_y, 0.05, 0.04])
        ax_stp = plt.axes([0.27, row_txt_y, 0.05, 0.04])
        
        self.box_min = TextBox(ax_min, 'Min ', initial=str(self.params['auto_min']), label_pad=0.02)
        self.box_max = TextBox(ax_max, 'Max ', initial=str(self.params['auto_max']), label_pad=0.02)
        self.box_step = TextBox(ax_stp, 'Step ', initial=str(self.params['auto_step']), label_pad=0.02)

        self.fig.text(0.36, row_txt_y + 0.02, "Plateau Stability:", fontsize=9, fontweight='bold')
        ax_rng = plt.axes([0.45, row_txt_y, 0.05, 0.04])
        ax_tol = plt.axes([0.53, row_txt_y, 0.05, 0.04])
        
        self.box_range = TextBox(ax_rng, '+/- nm ', initial=str(self.params['plat_range']), label_pad=0.05)
        self.box_tol   = TextBox(ax_tol, 'Tol % ', initial=str(self.params['plat_tol']), label_pad=0.05)

        # 3. ACTION BUTTONS
        ax_prev   = plt.axes([0.05, row_btn_y, 0.10, 0.05])
        ax_auto   = plt.axes([0.18, row_btn_y, 0.15, 0.05])
        ax_update = plt.axes([0.36, row_btn_y, 0.15, 0.05])
        ax_skip   = plt.axes([0.54, row_btn_y, 0.10, 0.05]) 
        ax_save   = plt.axes([0.67, row_btn_y, 0.20, 0.05])
        
        self.b_prev = Button(ax_prev, '< PREV', color='lightgray', hovercolor='silver')
        self.b_prev.on_clicked(self.prev_file)

        self.b_auto = Button(ax_auto, 'AUTO-TUNE', color='lightblue', hovercolor='skyblue')
        self.b_auto.on_clicked(self.run_auto_tune)

        self.b_update = Button(ax_update, 'FULL UPDATE', color='lightgray', hovercolor='silver')
        self.b_update.on_clicked(self.run_full_analysis) 
        
        self.b_skip = Button(ax_skip, 'SKIP >', color='salmon', hovercolor='red')
        self.b_skip.on_clicked(self.skip_file)
        
        self.b_save = Button(ax_save, 'SAVE & NEXT >>', color='lightgreen', hovercolor='lime')
        self.b_save.on_clicked(self.save_and_next)
        
        self.status_text = self.fig.text(0.5, 0.23, "Ready", ha='center', va='bottom', fontsize=11, fontweight='bold', color='#333333')
        
        # Connect text boxes
        self.box_min.on_submit(self.update_params)
        self.box_max.on_submit(self.update_params)
        self.box_step.on_submit(self.update_params)
        self.box_range.on_submit(self.update_params)
        self.box_tol.on_submit(self.update_params)
        
        plt.show()

    def update_params(self, text):
        """Callback to update parameters from text boxes."""
        try:
            self.params['auto_min'] = float(self.box_min.text)
            self.params['auto_max'] = float(self.box_max.text)
            self.params['auto_step'] = float(self.box_step.text)
            self.params['plat_range'] = float(self.box_range.text)
            self.params['plat_tol'] = float(self.box_tol.text)
        except ValueError:
            self.update_status("Invalid number in text box!", color='red')

    def update_view_only(self, event=None):
        """
        Fast Update: Updates binary mask visualization without running heavy graph analysis.
        Triggered by slider movement.
        """
        cutoff_val = self.s_thresh.val
        min_size = int(self.s_size.val)
        
        # 1. Fast Masking
        binary_mask = self.height_grid > cutoff_val
        if min_size > 1:
            cleaned_mask = remove_small_objects(binary_mask, min_size=min_size)
            cleaned_mask = clear_border(cleaned_mask)
        else:
            cleaned_mask = clear_border(binary_mask)
        
        self.current_mask = cleaned_mask
        
        # 2. Draw Raw Image
        self.ax_raw.clear()
        self.ax_raw.imshow(self.height_grid, cmap='gray')
        self.ax_raw.axis('off')
        
        # 3. Draw Mask Overlay (Fast)
        self.ax_skel.clear()
        self.ax_skel.imshow(np.ones_like(self.height_grid), cmap='gray', vmin=0, vmax=1)
        
        if np.any(cleaned_mask):
            blob_overlay = np.ma.masked_where(~cleaned_mask, cleaned_mask)
            cmap_blob = ListedColormap([COLOR_BLOB])
            self.ax_skel.imshow(blob_overlay, cmap=cmap_blob, alpha=1.0, interpolation='none', vmin=0, vmax=1)
            self.ax_skel.set_title("Preview (Click UPDATE for analysis)", fontsize=10, color='blue')
        else:
             self.ax_skel.set_title("Preview: No objects", fontsize=10)
             
        self.ax_skel.axis('off')
        self.fig.canvas.draw_idle()

    def run_full_analysis(self, event):
        """
        Full Analysis: Runs skeletonization, graph construction, and path finding.
        Triggered by 'FULL UPDATE' button.
        """
        self.update_status("Running analysis...", color='blue')
        self.fig.canvas.flush_events()
        
        self.valid_chains = [] 
        self.plot_lines = []

        if self.current_mask is None:
            self.update_view_only()

        # Efficient Background Calculation
        mask_flat = self.current_mask.ravel()
        data_flat = self.height_grid.ravel()
        bg_pixels = data_flat[~mask_flat]
        
        if bg_pixels.size > 0:
            self.bg_median = np.median(bg_pixels)
        else:
            self.bg_median = 0
            
        self.ax_raw.set_title(f"Raw Input (Bg: {self.bg_median:.2f} nm)", fontsize=10)

        # Skeletonization & Graph Analysis
        if np.any(self.current_mask):
            skeleton = skeletonize(self.current_mask)
            G = self.build_graph(skeleton)
            components = list(nx.connected_components(G))
            
            chain_counter = 1
            min_size = int(self.s_size.val)
            
            for comp_nodes in components:
                if len(comp_nodes) < min_size: continue
                
                G_mol = G.subgraph(comp_nodes).copy()
                structure_paths = self.analyze_structure(G_mol, chain_counter)
                
                for s_id, pixels in structure_paths.items():
                    # Unzip coordinates for plotting
                    y_coords, x_coords = zip(*pixels)
                    
                    color = COLOR_BACKBONE if s_id.endswith('_0') else COLOR_BRANCH
                    self.ax_skel.plot(x_coords, y_coords, color=color, linewidth=1.5)
                    self.plot_lines.append({'x': x_coords, 'y': y_coords, 'color': color})
                    
                    # Store Data points
                    for i, (r, c) in enumerate(pixels):
                         raw_h = self.height_grid[r, c]
                         self.valid_chains.append({
                            'filename': self.current_filename,
                            'structure_id': s_id,
                            'pixel_idx': i,
                            'x': c, 'y': r,
                            'raw_height_nm': raw_h,
                            'bg_median_nm': self.bg_median,
                            'height_nm': raw_h - self.bg_median
                        })
                if structure_paths: chain_counter += 1
                
            self.ax_skel.set_title(f"Analysis: {chain_counter-1} Chains Detected", fontsize=10)
        
        self.fig.canvas.draw_idle()
        self.update_status("Analysis Complete", color='green')

    def run_auto_tune(self, event):
        """
        Auto-Tune Algorithm: Scans height thresholds to find a stable plateau in fiber count.
        Uses downsampling for speed.
        """
        self.update_status("Scanning... (Optimized)", color='darkorange')
        self.fig.canvas.flush_events() 
        
        try:
            start_h = float(self.box_min.text)
            end_h = float(self.box_max.text)
            step_h = float(self.box_step.text)
            plat_range = float(self.box_range.text)
            plat_tol = float(self.box_tol.text)
        except:
            self.update_status("Error reading params", color='red')
            return

        # Optimization: Downsample image for auto-tune logic
        small_grid = rescale(self.height_grid, AUTO_TUNE_DOWNSAMPLE, anti_aliasing=False, preserve_range=True)
        min_size_scaled = int(self.s_size.val * AUTO_TUNE_DOWNSAMPLE)
        
        test_heights = np.arange(start_h, end_h, step_h)
        results = []

        # Loop through thresholds
        for h in test_heights:
            binary_mask = small_grid > h
            if min_size_scaled > 1:
                cleaned = remove_small_objects(binary_mask, min_size=min_size_scaled)
            else:
                cleaned = binary_mask
                
            if not np.any(cleaned):
                results.append(0)
                continue
            
            # Count connected components
            _, count = label(cleaned, return_num=True)
            results.append(count)
        
        results = np.array(results)
        
        # Find Plateau
        best_thresh = None
        max_stable_count = 0
        
        for i in range(len(test_heights)):
            center_h = test_heights[i]
            center_val = results[i] 
            if center_val == 0: continue
            
            indices = np.where((test_heights >= center_h - plat_range) & 
                               (test_heights <= center_h + plat_range))[0]
            
            if len(indices) < 3: continue 
            
            vals = results[indices]
            pct_changes = np.abs(vals - center_val) / center_val * 100
            
            if np.all(pct_changes <= plat_tol):
                if center_val > max_stable_count:
                    max_stable_count = center_val
                    best_thresh = center_h

        if best_thresh is not None:
            self.s_thresh.set_val(best_thresh)
            self.update_status(f"Auto-Tune: {best_thresh:.2f} nm (Approx Count: {int(max_stable_count)})", color='green')
            # Trigger full analysis on the full-res image using the new threshold
            self.run_full_analysis(None)
        else:
            self.update_status("No stable plateau found.", color='red')

    # --- NAVIGATION ---
    def prev_file(self, event):
        if self.current_idx > 0:
            self.current_idx -= 1
            plt.close(self.fig)
            self.load_next_image()

    def skip_file(self, event):
        self.current_idx += 1
        plt.close(self.fig)
        self.load_next_image()

    def save_and_next(self, event):
        if not self.valid_chains:
            self.update_status("No data to save. Run Update first!", color='red')
            return
            
        base_name = self.current_filename 
        excel_path = os.path.join(self.output_folder, f"{base_name}_results.xlsx")
        raw_img_path = os.path.join(self.output_folder, f"{base_name}_raw.png")
        skel_img_path = os.path.join(self.output_folder, f"{base_name}_skeletonized.png")
        
        # Export Data
        df = pd.DataFrame(self.valid_chains)
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            df[['filename', 'structure_id', 'pixel_idx', 'height_nm', 'raw_height_nm', 'bg_median_nm']].to_excel(writer, sheet_name='fiber_height', index=False)
            df[['filename', 'structure_id', 'pixel_idx', 'x', 'y']].to_excel(writer, sheet_name='path_coordinates', index=False)
        
        self.save_images(raw_img_path, skel_img_path)
        self.update_status(f"Saved: {base_name}", color='blue')
        plt.pause(0.2)
        
        self.current_idx += 1
        plt.close(self.fig)
        self.load_next_image()

    # --- HELPER FUNCTIONS ---
    def save_images(self, raw_path, skel_path):
        """Saves the raw AFM image and the skeletonized overlay."""
        h, w = self.height_grid.shape
        dpi = 300
        
        # Save Raw
        fig_raw, ax_raw = plt.subplots(figsize=(w/100, h/100), dpi=dpi)
        ax_raw.axis('off')
        ax_raw.imshow(self.height_grid, cmap='gray')
        plt.subplots_adjust(0,0,1,1,0,0)
        ax_raw.margins(0,0)
        fig_raw.savefig(raw_path, bbox_inches='tight', pad_inches=0)
        plt.close(fig_raw)

        # Save Skeleton
        fig_skel, ax_skel = plt.subplots(figsize=(w/100, h/100), dpi=dpi)
        ax_skel.axis('off')
        ax_skel.imshow(np.ones_like(self.height_grid), cmap='gray', vmin=0, vmax=1)
        if self.current_mask is not None:
            blob_overlay = np.ma.masked_where(~self.current_mask, self.current_mask)
            cmap_blob = ListedColormap([COLOR_BLOB])
            ax_skel.imshow(blob_overlay, cmap=cmap_blob, alpha=1.0, interpolation='none')
        for line in self.plot_lines:
            ax_skel.plot(line['x'], line['y'], color=line['color'], linewidth=1.5)
        plt.subplots_adjust(0,0,1,1,0,0)
        ax_skel.margins(0,0)
        fig_skel.savefig(skel_path, bbox_inches='tight', pad_inches=0)
        plt.close(fig_skel)

    def build_graph(self, skeleton_img):
        """Converts a skeleton image into a NetworkX graph."""
        G = nx.Graph()
        rows, cols = skeleton_img.shape
        r_idx, c_idx = np.where(skeleton_img)
        for r, c in zip(r_idx, c_idx):
            G.add_node((r, c))
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0: continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        if skeleton_img[nr, nc]:
                            G.add_edge((r, c), (nr, nc))
        return G

    def analyze_structure(self, G_sub, chain_idx):
        """
        Identifies the backbone and branches of a connected graph component.
        - Backbone: Longest shortest path between endpoints.
        - Branches: Paths extending from the backbone.
        """
        paths = {}
        endpoints = [n for n in G_sub.nodes() if G_sub.degree(n) == 1]
        if len(endpoints) < 2: return {f"{chain_idx}_0": list(G_sub.nodes())}
        
        # Find Longest Path (Backbone)
        try:
            start = endpoints[0]
            dists = nx.single_source_shortest_path_length(G_sub, start)
            u = max(dists, key=dists.get)
            dists_u = nx.single_source_shortest_path_length(G_sub, u)
            v = max(dists_u, key=dists_u.get)
            backbone = nx.shortest_path(G_sub, u, v)
            paths[f"{chain_idx}_0"] = backbone
        except: return {}
        
        visited = set(backbone)
        branch_count = 1
        
        # Find Branches
        for node in backbone:
            for neighbor in G_sub.neighbors(node):
                if neighbor not in visited:
                    branch_nodes = []
                    queue = [neighbor]
                    visited.add(neighbor)
                    while queue:
                        curr = queue.pop(0)
                        branch_nodes.append(curr)
                        for n in G_sub.neighbors(curr):
                            if n not in visited:
                                visited.add(n)
                                queue.append(n)
                    
                    G_branch = G_sub.subgraph(branch_nodes + [node])
                    try:
                        d = nx.single_source_shortest_path_length(G_branch, node)
                        valid_d = {k:v for k,v in d.items() if k in branch_nodes}
                        tip = max(valid_d, key=valid_d.get)
                        branch_path = nx.shortest_path(G_branch, node, tip)
                        branch_path.remove(node)
                        paths[f"{chain_idx}_{branch_count}"] = branch_path
                        branch_count += 1
                    except: continue
        return paths

if __name__ == "__main__":
    app = HeightFilterTool(INPUT_FOLDER, OUTPUT_FOLDER)