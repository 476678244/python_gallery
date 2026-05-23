from spire.presentation import Presentation, FileFormat
import os

def preview_pptx_spire(pptx_path, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # 初始化 Presentation 对象
    pres = Presentation()
    pres.LoadFromFile(pptx_path)
    
    for i in range(pres.Slides.Count):
        slide = pres.Slides[i]
        # 将幻灯片保存为图像
        image = slide.SaveAsImage()
        output_path = os.path.join(output_folder, f"slide_{i+1:02d}.png")
        image.Save(output_path)
        print(f"Slide {i+1} saved to {output_path}")
    
    pres.Dispose()

if __name__ == "__main__":
    PPT_PATH = "/basic/homework/mp4_to_ppt/24节气_v3.pptx"
    OUT_DIR = "/basic/homework/mp4_to_ppt/previews_spire"
    preview_pptx_spire(PPT_PATH, OUT_DIR)
