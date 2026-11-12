"""
AFMPL v.3.0.0.
----------------------------------------
A GUI-based tool for analyzing AFM images.
Features:
- Loads Bruker AFM files using pySPM.
- Preprocesses images (line/plane correction, scar removal).
- Dual-segments fibers and aggregates based on height thresholds.
- Skeletonizes fibers and separates backbones from branches.
- Extracts Aggregate properties (Area, Exact Volume, Max Height).
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

# Added binary_dilation here
from skimage.morphology import skeletonize, remove_small_objects, binary_erosion, binary_dilation, disk
from skimage.segmentation import clear_border
from skimage.measure import label, regionprops
from skimage.transform import rescale

# --- CONFIGURATION ---
INPUT_FOLDER = r'Y:\your_project\afm_data\input'
OUTPUT_FOLDER = r'Y:\your_project\afm_data\output'

# --- DEFAULT SETTINGS ---
DEFAULT_FIBER_SIGMA = 2.0    # Standard deviations above background for fibers
DEFAULT_AGG_SIGMA = 9.0    # Standard deviations above background for aggregates

# --- VISUALIZATION COLORS ---
COLOR_FIBER_MASK = 'darkred'
COLOR_AGG_MASK = 'orange'
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
        
        self.params = {
            'min_size': 10,
            'fiber_sigma': DEFAULT_FIBER_SIGMA,
            'agg_sigma': DEFAULT_AGG_SIGMA
        }
        
        self.valid_chains = [] 
        self.valid_aggregates = []
        self.mask_fibers = None
        self.mask_aggs = None
        self.plot_lines = [] 
        self.bg_median = 0.0 
        
        print("Starting AFM Height Filter Tool...")
        self.load_next_image()

    def load_next_image(self):
        if self.current_idx < 0: self.current_idx = 0
        if self.current_idx >= len(self.files):
            print("All files processed!")
            plt.close('all')
            return

        self.valid_chains = [] 
        self.valid_aggregates = []
        self.plot_lines = []
        self.mask_fibers = None
        self.mask_aggs = None
        gc.collect() 

        self.current_filename = self.files[self.current_idx]
        file_path = os.path.join(self.input_folder, self.current_filename)
        
        try:
            image = pySPM.Bruker(file_path)
            height = image.get_channel("Height")
            
            # 1. Initial 1st-order plane correction and scar removal
            top = height.correct_plane(inline=False)
            top = top.filter_scars_removal(.7, inline=False)
            
            # 2. Fix scanner bowing with a 2nd-order polynomial fit BEFORE line correction
            top = top.corr_fit2d(nx=2, ny=2, inline=False)
            top = top.correct_lines(inline=False)
            
            # 3. Create a feature mask now that the heavy bowing is gone
            mask0 = top.get_bin_threshold(.1, high=False)
            mask1 = binary_erosion(mask0, disk(3))
            
            # 4. Final masked polynomial fit (background only) for a perfectly flat baseline
            top = top.corr_fit2d(nx=2, ny=2, mask=mask1, inline=False)
            top = top.filter_scars_removal(.7, inline=False)
            top = top.correct_lines(inline=False).zero_min()
            
            self.height_grid = top.pixels
            
            self.setup_gui()
            self.update_status(f"Loaded: {self.current_filename} ({self.current_idx + 1}/{len(self.files)})")
            self.update_view_only()

        except Exception as e:
            print(f"Failed to load {self.current_filename}: {e}")
            self.current_idx += 1
            self.load_next_image()

    def update_status(self, text, color='black'):
        if hasattr(self, 'status_text'):
            self.status_text.set_text(text)
            self.status_text.set_color(color)
            self.fig.canvas.draw_idle()
        print(f"[Status] {text}") 

    def setup_gui(self):
        plt.close('all')
        self.fig = plt.figure(figsize=(18, 9), facecolor=COLOR_BG_APP)
        self.fig.canvas.manager.set_window_title(f"AFM Analysis - {self.current_filename}")
                
        gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1], hspace=0.3)
        
        gs_images = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=gs[0], wspace=0.1)
        self.ax_raw = self.fig.add_subplot(gs_images[0])
        self.ax_skel = self.fig.add_subplot(gs_images[1])
        
        row_btn_y = 0.03
        row_txt_y = 0.10
        row_sld_y = 0.20
                
        # SLIDERS
        ax_thresh = plt.axes([0.15, row_sld_y, 0.30, 0.03], facecolor='white')
        ax_agg_thresh = plt.axes([0.15, row_sld_y - 0.04, 0.30, 0.03], facecolor='white')
        ax_size   = plt.axes([0.55, row_sld_y - 0.02, 0.30, 0.03], facecolor='white')
        
        h_min, h_max = np.min(self.height_grid), np.max(self.height_grid)
        
        self.s_thresh = Slider(ax_thresh, 'Fiber Threshold', h_min, h_max, valinit=0.5, color=COLOR_FIBER_MASK) 
        self.s_agg_thresh = Slider(ax_agg_thresh, 'Agg Threshold', h_min, h_max, valinit=2.0, color=COLOR_AGG_MASK) 
        self.s_size = Slider(ax_size, 'Min Size (px)', 1, 100, valinit=self.params['min_size'], valstep=1, color='gray')

        self.s_thresh.on_changed(self.update_view_only)
        self.s_agg_thresh.on_changed(self.update_view_only)
        self.s_size.on_changed(self.update_view_only)

        # TEXT BOXES (Updated for Statistical Auto-Tune)
        self.fig.text(0.15, row_txt_y + 0.02, "Auto-Tune Sensitivity (Sigma):", fontsize=9, fontweight='bold')
        ax_fib_sig = plt.axes([0.15, row_txt_y - 0.02, 0.08, 0.04])
        ax_agg_sig = plt.axes([0.25, row_txt_y - 0.02, 0.08, 0.04])
        
        self.box_fib_sig = TextBox(ax_fib_sig, 'Fiber ', initial=str(self.params['fiber_sigma']), label_pad=0.02)
        self.box_agg_sig = TextBox(ax_agg_sig, 'Agg ', initial=str(self.params['agg_sigma']), label_pad=0.02)

        # BUTTONS
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
        
        self.status_text = self.fig.text(0.5, 0.25, "Ready", ha='center', va='bottom', fontsize=11, fontweight='bold', color='#333333')
        
        self.box_fib_sig.on_submit(self.update_params)
        self.box_agg_sig.on_submit(self.update_params)
        
        plt.show()

    def update_params(self, text):
        try:
            self.params['fiber_sigma'] = float(self.box_fib_sig.text)
            self.params['agg_sigma'] = float(self.box_agg_sig.text)
        except ValueError:
            self.update_status("Invalid number in text box!", color='red')

    def update_view_only(self, event=None):
        fiber_val = self.s_thresh.val
        agg_val = self.s_agg_thresh.val
        min_size = int(self.s_size.val)
        
        # 1. Masking
        mask_all = self.height_grid > fiber_val
        mask_agg = self.height_grid > agg_val
        
        if min_size > 1:
            mask_all = remove_small_objects(mask_all, min_size=min_size)
            mask_agg = remove_small_objects(mask_agg, min_size=min_size)
            
        mask_all = clear_border(mask_all)
        mask_agg = clear_border(mask_agg)
        
        # Dilate the aggregate mask slightly to encompass its sloping base (the halo)
        agg_halo = binary_dilation(mask_agg, disk(4))
        
        # Isolate pure fibers by subtracting the expanded aggregate halo
        mask_fibers = mask_all & ~agg_halo
        
        self.mask_fibers = mask_fibers
        self.mask_aggs = mask_agg
        
        # 2. Draw Raw Image
        self.ax_raw.clear()
        self.ax_raw.imshow(self.height_grid, cmap='gray')
        self.ax_raw.axis('off')
        
        # 3. Draw Mask Overlay 
        self.ax_skel.clear()
        self.ax_skel.imshow(np.ones_like(self.height_grid), cmap='gray', vmin=0, vmax=1)
        
        if np.any(mask_fibers):
            overlay_f = np.ma.masked_where(~mask_fibers, mask_fibers)
            self.ax_skel.imshow(overlay_f, cmap=ListedColormap([COLOR_FIBER_MASK]), alpha=1.0, interpolation='none')
            
        if np.any(mask_agg):
            overlay_a = np.ma.masked_where(~mask_agg, mask_agg)
            self.ax_skel.imshow(overlay_a, cmap=ListedColormap([COLOR_AGG_MASK]), alpha=1.0, interpolation='none')
            
        if np.any(mask_fibers) or np.any(mask_agg):
            self.ax_skel.set_title("Preview (Red: Fibers, Orange: Aggregates)", fontsize=10, color='blue')
        else:
             self.ax_skel.set_title("Preview: No objects", fontsize=10)
             
        self.ax_skel.axis('off')
        self.fig.canvas.draw_idle()

    def run_full_analysis(self, event):
        self.update_status("Running analysis...", color='blue')
        self.fig.canvas.flush_events()
        
        self.valid_chains = [] 
        self.valid_aggregates = []
        self.plot_lines = []

        if self.mask_fibers is None or self.mask_aggs is None:
            self.update_view_only()

        # Background Calculation (Pixels not in either mask)
        mask_all = self.mask_fibers | self.mask_aggs
        bg_pixels = self.height_grid[~mask_all]
        self.bg_median = np.median(bg_pixels) if bg_pixels.size > 0 else 0.0
            
        self.ax_raw.set_title(f"Raw Input (Bg: {self.bg_median:.2f} nm)", fontsize=10)

        # 1. PROCESS AGGREGATES
        if np.any(self.mask_aggs):
            label_agg = label(self.mask_aggs)
            props = regionprops(label_agg, intensity_image=self.height_grid)
            
            for p in props:
                agg_area = p.area
                
                # --- FIX: Exact pixel-by-pixel volume calculation ---
                coords = p.coords 
                
                # Extract their heights and subtract the background median
                pixel_heights = self.height_grid[coords[:, 0], coords[:, 1]] - self.bg_median
                
                # Calculate exact volume by summing the heights of every pixel
                exact_volume = np.sum(pixel_heights)
                
                max_h = p.max_intensity - self.bg_median
                mean_h = np.mean(pixel_heights)
                
                self.valid_aggregates.append({
                    'filename': self.current_filename,
                    'aggregate_id': p.label,
                    'centroid_x': p.centroid[1],
                    'centroid_y': p.centroid[0],
                    'area_px': agg_area,
                    'mean_height_nm': mean_h,
                    'max_height_nm': max_h,
                    'volume_exact': exact_volume
                })

        # 2. PROCESS FIBERS
        chain_counter = 1
        if np.any(self.mask_fibers):
            skeleton = skeletonize(self.mask_fibers)
            G = self.build_graph(skeleton)
            components = list(nx.connected_components(G))
            min_size = int(self.s_size.val)
            
            for comp_nodes in components:
                if len(comp_nodes) < min_size: continue
                
                G_mol = G.subgraph(comp_nodes).copy()
                structure_paths = self.analyze_structure(G_mol, chain_counter)
                
                for s_id, pixels in structure_paths.items():
                    y_coords, x_coords = zip(*pixels)
                    color = COLOR_BACKBONE if s_id.endswith('_0') else COLOR_BRANCH
                    
                    self.ax_skel.plot(x_coords, y_coords, color=color, linewidth=1.5)
                    self.plot_lines.append({'x': x_coords, 'y': y_coords, 'color': color})
                    
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
                
        self.ax_skel.set_title(f"Analysis: {chain_counter-1} Chains, {len(self.valid_aggregates)} Aggregates", fontsize=10)
        self.fig.canvas.draw_idle()
        self.update_status("Analysis Complete", color='green')

    def run_auto_tune(self, event):
        """Robust statistical auto-tune using Median Absolute Deviation (MAD)."""
        self.update_status("Calculating robust thresholds...", color='darkorange')
        self.fig.canvas.flush_events() 
        
        try:
            f_sig = float(self.box_fib_sig.text)
            a_sig = float(self.box_agg_sig.text)
        except:
            self.update_status("Error reading sigma params", color='red')
            return

        flat_data = self.height_grid.ravel()
        median = np.median(flat_data)
        
        # Calculate standard deviation robustly (ignoring tall peaks)
        mad = np.median(np.abs(flat_data - median))
        std_est = mad * 1.4826
        
        best_fiber = median + (f_sig * std_est)
        best_agg = median + (a_sig * std_est)
        
        self.s_thresh.set_val(best_fiber)
        self.s_agg_thresh.set_val(best_agg)
        
        self.update_status(f"Auto-Tune: Fiber {best_fiber:.2f}nm, Agg {best_agg:.2f}nm", color='green')
        self.run_full_analysis(None)

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
        if not self.valid_chains and not self.valid_aggregates:
            self.update_status("No data to save. Run Update first!", color='red')
            return
            
        base_name = self.current_filename 
        excel_path = os.path.join(self.output_folder, f"{base_name}_results.xlsx")
        raw_img_path = os.path.join(self.output_folder, f"{base_name}_raw.png")
        skel_img_path = os.path.join(self.output_folder, f"{base_name}_skeletonized.png")
        
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            if self.valid_chains:
                df_chains = pd.DataFrame(self.valid_chains)
                df_chains[['filename', 'structure_id', 'pixel_idx', 'height_nm', 'raw_height_nm', 'bg_median_nm']].to_excel(writer, sheet_name='fiber_height', index=False)
                df_chains[['filename', 'structure_id', 'pixel_idx', 'x', 'y']].to_excel(writer, sheet_name='path_coordinates', index=False)
            
            if self.valid_aggregates:
                df_aggs = pd.DataFrame(self.valid_aggregates)
                df_aggs.to_excel(writer, sheet_name='aggregates', index=False)
        
        self.save_images(raw_img_path, skel_img_path)
        self.update_status(f"Saved: {base_name}", color='blue')
        plt.pause(0.2)
        
        self.current_idx += 1
        plt.close(self.fig)
        self.load_next_image()

    # --- HELPER FUNCTIONS ---
    def save_images(self, raw_path, skel_path):
        h, w = self.height_grid.shape
        dpi = 200
        
        fig_raw, ax_raw = plt.subplots(figsize=(w/100, h/100), dpi=dpi)
        ax_raw.axis('off')
        ax_raw.imshow(self.height_grid, cmap='gray')
        plt.subplots_adjust(0,0,1,1,0,0)
        ax_raw.margins(0,0)
        fig_raw.savefig(raw_path, bbox_inches='tight', pad_inches=0)
        plt.close(fig_raw)

        fig_skel, ax_skel = plt.subplots(figsize=(w/100, h/100), dpi=dpi)
        ax_skel.axis('off')
        ax_skel.imshow(np.ones_like(self.height_grid), cmap='gray', vmin=0, vmax=1)
        
        if self.mask_fibers is not None:
            overlay_f = np.ma.masked_where(~self.mask_fibers, self.mask_fibers)
            ax_skel.imshow(overlay_f, cmap=ListedColormap([COLOR_FIBER_MASK]), alpha=1.0, interpolation='none')
            
        if self.mask_aggs is not None:
            overlay_a = np.ma.masked_where(~self.mask_aggs, self.mask_aggs)
            ax_skel.imshow(overlay_a, cmap=ListedColormap([COLOR_AGG_MASK]), alpha=1.0, interpolation='none')

        for line in self.plot_lines:
            ax_skel.plot(line['x'], line['y'], color=line['color'], linewidth=1.5)
            
        plt.subplots_adjust(0,0,1,1,0,0)
        ax_skel.margins(0,0)
        fig_skel.savefig(skel_path, bbox_inches='tight', pad_inches=0)
        plt.close(fig_skel)

    def build_graph(self, skeleton_img):
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
        paths = {}
        endpoints = [n for n in G_sub.nodes() if G_sub.degree(n) == 1]
        if len(endpoints) < 2: return {f"{chain_idx}_0": list(G_sub.nodes())}
        
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