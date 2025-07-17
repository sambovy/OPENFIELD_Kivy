import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.filechooser import FileChooserListView
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
import time
import os

# Definindo o tamanho mínimo da janela
Window.minimum_width = 1200
Window.minimum_height = 700

class OpenFieldApp(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.padding = 10
        self.spacing = 10
        
        # Variáveis de controle do teste
        self.test_running = False
        self.start_time = None
        self.remaining_time = 0
        self.test_duration = 300  # Duração padrão em segundos
        self.animal_id = ""
        
        # Variáveis para armazenar o tempo acumulado em cada área
        self.corner_time = 0.0
        self.lateral_time = 0.0
        self.center_time = 0.0
        
        # Variáveis para controlar se um botão de área está atualmente pressionado
        self.corner_button_pressed = False
        self.lateral_button_pressed = False
        self.center_button_pressed = False
        
        # Variáveis para registrar o tempo de início da pressão do botão
        self.corner_press_time = None
        self.lateral_press_time = None
        self.center_press_time = None
        
        self.test_data = {}  # Para armazenar os resultados do teste atual
        
        # Evento do Clock para atualizar o timer
        self.timer_event = None
        
        self.create_widgets()
    
    def create_widgets(self):
        # Coluna da esquerda - Aplicação de Teste
        left_column = BoxLayout(orientation='vertical', spacing=10, size_hint_x=0.5)
        
        # Frame de Configuração
        config_layout = BoxLayout(orientation='vertical', spacing=5, size_hint_y=0.3)
        config_layout.add_widget(Label(text='Configurações do Teste', size_hint_y=0.2, bold=True))
        
        # ID do Animal
        id_layout = BoxLayout(orientation='horizontal', size_hint_y=0.4)
        id_layout.add_widget(Label(text='ID do Animal:', size_hint_x=0.4))
        self.animal_id_input = TextInput(multiline=False, size_hint_x=0.6)
        id_layout.add_widget(self.animal_id_input)
        config_layout.add_widget(id_layout)
        
        # Duração do Teste
        duration_layout = BoxLayout(orientation='horizontal', size_hint_y=0.4)
        duration_layout.add_widget(Label(text='Duração (segundos):', size_hint_x=0.4))
        self.duration_input = TextInput(text='300', multiline=False, size_hint_x=0.6)
        duration_layout.add_widget(self.duration_input)
        config_layout.add_widget(duration_layout)
        
        left_column.add_widget(config_layout)
        
        # Frame de Controle do Teste
        control_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=0.3)
        
        # Timer
        self.timer_label = Label(text='Tempo Restante: 00:00', font_size=24, size_hint_y=0.5)
        control_layout.add_widget(self.timer_label)
        
        # Botões de controle
        buttons_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.5)
        self.start_button = Button(text='Iniciar Teste', size_hint_x=0.5)
        self.start_button.bind(on_press=self.start_test)
        self.start_button.background_color = (0, 0.8, 0, 1)  # Verde
        
        self.stop_button = Button(text='Parar Teste', size_hint_x=0.5, disabled=True)
        self.stop_button.bind(on_press=self.stop_test)
        self.stop_button.background_color = (0.8, 0, 0, 1)  # Vermelho
        
        buttons_layout.add_widget(self.start_button)
        buttons_layout.add_widget(self.stop_button)
        control_layout.add_widget(buttons_layout)
        
        left_column.add_widget(control_layout)
        
        # Frame de Marcação de Áreas
        area_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=0.4)
        area_layout.add_widget(Label(text='Marcação de Áreas (Pressione e Segure)', size_hint_y=0.15, bold=True))
        
        # Botões das áreas
        area_buttons_layout = GridLayout(cols=2, spacing=10, size_hint_y=0.4)
        
        self.corner_btn = Button(text='Canto', disabled=True)
        self.corner_btn.background_color = (0.8, 0, 0, 1)  # Vermelho
        self.corner_btn.bind(on_press=self.on_corner_press)
        self.corner_btn.bind(on_release=self.on_corner_release)
        
        self.lateral_btn = Button(text='Lateral', disabled=True)
        self.lateral_btn.background_color = (0.5, 0.8, 1, 1)  # Azul claro
        self.lateral_btn.bind(on_press=self.on_lateral_press)
        self.lateral_btn.bind(on_release=self.on_lateral_release)
        
        area_buttons_layout.add_widget(self.corner_btn)
        area_buttons_layout.add_widget(self.lateral_btn)
        area_layout.add_widget(area_buttons_layout)
        
        # Botão do centro (ocupa toda a largura)
        self.center_btn = Button(text='Centro', disabled=True, size_hint_y=0.2)
        self.center_btn.background_color = (0, 0.6, 0, 1)  # Verde floresta
        self.center_btn.bind(on_press=self.on_center_press)
        self.center_btn.bind(on_release=self.on_center_release)
        area_layout.add_widget(self.center_btn)
        
        # Labels para exibir os tempos
        times_layout = BoxLayout(orientation='vertical', spacing=5, size_hint_y=0.25)
        self.corner_time_label = Label(text='Tempo no Canto: 0.00 s')
        self.lateral_time_label = Label(text='Tempo na Lateral: 0.00 s')
        self.center_time_label = Label(text='Tempo no Centro: 0.00 s')
        
        times_layout.add_widget(self.corner_time_label)
        times_layout.add_widget(self.lateral_time_label)
        times_layout.add_widget(self.center_time_label)
        area_layout.add_widget(times_layout)
        
        left_column.add_widget(area_layout)
        
        # Coluna da direita - Relatório e Gráfico
        right_column = BoxLayout(orientation='vertical', spacing=10, size_hint_x=0.5)
        
        # Frame de Relatório
        report_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=0.5)
        report_layout.add_widget(Label(text='Relatório do Teste', size_hint_y=0.1, bold=True))
        
        # Área de texto do relatório
        self.report_text = TextInput(readonly=True, size_hint_y=0.8)
        report_layout.add_widget(self.report_text)
        
        # Botões de relatório
        report_buttons_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.1)
        
        generate_report_btn = Button(text='Gerar/Atualizar Relatório')
        generate_report_btn.bind(on_press=self.generate_report)
        
        export_report_btn = Button(text='Exportar Relatório (TXT)')
        export_report_btn.bind(on_press=self.export_report)
        
        report_buttons_layout.add_widget(generate_report_btn)
        report_buttons_layout.add_widget(export_report_btn)
        report_layout.add_widget(report_buttons_layout)
        
        right_column.add_widget(report_layout)
        
        # Frame do Gráfico
        chart_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=0.5)
        chart_layout.add_widget(Label(text='Distribuição de Tempo por Área', size_hint_y=0.1, bold=True))
        
        # Área do gráfico
        self.chart_container = BoxLayout(orientation='vertical', size_hint_y=0.9)
        chart_layout.add_widget(self.chart_container)
        
        right_column.add_widget(chart_layout)
        
        # Adiciona as colunas ao layout principal
        self.add_widget(left_column)
        self.add_widget(right_column)
    
    def start_test(self, instance):
        if self.test_running:
            return
        
        # Validação dos dados de entrada
        animal_id = self.animal_id_input.text.strip()
        if not animal_id:
            self.show_popup("Erro", "Por favor, insira o ID do Animal.")
            return
        
        try:
            duration = int(self.duration_input.text)
            if duration <= 0:
                raise ValueError
        except ValueError:
            self.show_popup("Erro", "Por favor, insira uma duração de teste válida.")
            return
        
        # Inicializa o teste
        self.test_running = True
        self.start_time = time.time()
        self.remaining_time = duration
        self.test_duration = duration
        self.animal_id = animal_id
        
        # Reset dos tempos e estados
        self.corner_time = 0.0
        self.lateral_time = 0.0
        self.center_time = 0.0
        self.corner_button_pressed = False
        self.lateral_button_pressed = False
        self.center_button_pressed = False
        self.corner_press_time = None
        self.lateral_press_time = None
        self.center_press_time = None
        self.test_data = {}
        
        self.update_area_time_labels()
        
        # Atualiza os botões
        self.start_button.disabled = True
        self.stop_button.disabled = False
        self.corner_btn.disabled = False
        self.lateral_btn.disabled = False
        self.center_btn.disabled = False
        
        # Limpa o gráfico anterior
        self.chart_container.clear_widgets()
        
        # Inicia o timer
        self.timer_event = Clock.schedule_interval(self.update_timer, 0.2)
    
    def stop_test(self, instance=None, manual_stop=True):
        if not self.test_running:
            return
        
        self.test_running = False
        
        # Para o timer
        if self.timer_event:
            self.timer_event.cancel()
        
        # Atualiza os botões
        self.start_button.disabled = False
        self.stop_button.disabled = True
        self.corner_btn.disabled = True
        self.lateral_btn.disabled = True
        self.center_btn.disabled = True
        
        # Garante que qualquer tempo ativo seja contabilizado
        if self.corner_button_pressed:
            self.on_corner_release(None)
        if self.lateral_button_pressed:
            self.on_lateral_release(None)
        if self.center_button_pressed:
            self.on_center_release(None)
        
        self.update_area_time_labels()
        self.generate_report(None)
        
        if manual_stop:
            self.show_popup("Teste Finalizado", f"Teste para {self.animal_id} finalizado!")
    
    def update_timer(self, dt):
        if self.test_running:
            elapsed_total_time = time.time() - self.start_time
            self.remaining_time = self.test_duration - elapsed_total_time
            
            # Atualiza os tempos das áreas em tempo real
            if self.corner_button_pressed and self.corner_press_time:
                current_press_duration = time.time() - self.corner_press_time
                self.corner_time_label.text = f"Tempo no Canto: {self.corner_time + current_press_duration:.2f} s"
            
            if self.lateral_button_pressed and self.lateral_press_time:
                current_press_duration = time.time() - self.lateral_press_time
                self.lateral_time_label.text = f"Tempo na Lateral: {self.lateral_time + current_press_duration:.2f} s"
            
            if self.center_button_pressed and self.center_press_time:
                current_press_duration = time.time() - self.center_press_time
                self.center_time_label.text = f"Tempo no Centro: {self.center_time + current_press_duration:.2f} s"
            
            if self.remaining_time <= 0:
                self.remaining_time = 0
                self.timer_label.text = "Tempo Restante: 00:00"
                self.stop_test(manual_stop=False)
                return False
            
            mins = int(self.remaining_time // 60)
            secs = int(self.remaining_time % 60)
            self.timer_label.text = f"Tempo Restante: {mins:02d}:{secs:02d}"
        
        return True
    
    def on_corner_press(self, instance):
        if self.test_running and not self.corner_button_pressed:
            self.stop_other_buttons('corner')
            self.corner_button_pressed = True
            self.corner_press_time = time.time()
            self.highlight_button(self.corner_btn, True)
    
    def on_corner_release(self, instance):
        if self.test_running and self.corner_button_pressed:
            elapsed = time.time() - self.corner_press_time
            self.corner_time += elapsed
            self.corner_button_pressed = False
            self.corner_press_time = None
            self.update_area_time_labels()
            self.highlight_button(self.corner_btn, False)
    
    def on_lateral_press(self, instance):
        if self.test_running and not self.lateral_button_pressed:
            self.stop_other_buttons('lateral')
            self.lateral_button_pressed = True
            self.lateral_press_time = time.time()
            self.highlight_button(self.lateral_btn, True)
    
    def on_lateral_release(self, instance):
        if self.test_running and self.lateral_button_pressed:
            elapsed = time.time() - self.lateral_press_time
            self.lateral_time += elapsed
            self.lateral_button_pressed = False
            self.lateral_press_time = None
            self.update_area_time_labels()
            self.highlight_button(self.lateral_btn, False)
    
    def on_center_press(self, instance):
        if self.test_running and not self.center_button_pressed:
            self.stop_other_buttons('center')
            self.center_button_pressed = True
            self.center_press_time = time.time()
            self.highlight_button(self.center_btn, True)
    
    def on_center_release(self, instance):
        if self.test_running and self.center_button_pressed:
            elapsed = time.time() - self.center_press_time
            self.center_time += elapsed
            self.center_button_pressed = False
            self.center_press_time = None
            self.update_area_time_labels()
            self.highlight_button(self.center_btn, False)
    
    def stop_other_buttons(self, current_button):
        if current_button != 'corner' and self.corner_button_pressed:
            self.on_corner_release(None)
        if current_button != 'lateral' and self.lateral_button_pressed:
            self.on_lateral_release(None)
        if current_button != 'center' and self.center_button_pressed:
            self.on_center_release(None)
    
    def highlight_button(self, button, is_pressed):
        if is_pressed:
            button.background_color = (0.3, 0.3, 0.3, 1)  # Cinza escuro
        else:
            # Restaura a cor original
            if button == self.corner_btn:
                button.background_color = (0.8, 0, 0, 1)  # Vermelho
            elif button == self.lateral_btn:
                button.background_color = (0.5, 0.8, 1, 1)  # Azul claro
            elif button == self.center_btn:
                button.background_color = (0, 0.6, 0, 1)  # Verde floresta
    
    def update_area_time_labels(self):
        self.corner_time_label.text = f"Tempo no Canto: {self.corner_time:.2f} s"
        self.lateral_time_label.text = f"Tempo na Lateral: {self.lateral_time:.2f} s"
        self.center_time_label.text = f"Tempo no Centro: {self.center_time:.2f} s"
    
    def generate_report(self, instance):
        if not self.start_time:
            self.show_popup("Aviso", "Inicie um teste primeiro para gerar o relatório.")
            return
        
        # Calcula a duração efetiva do teste
        if self.test_running:
            effective_duration = time.time() - self.start_time
        else:
            effective_duration = self.test_duration - self.remaining_time
        
        if effective_duration <= 0:
            effective_duration = 0.001
        
        # Calcula as porcentagens
        corner_percent = (self.corner_time / effective_duration) * 100
        lateral_percent = (self.lateral_time / effective_duration) * 100
        center_percent = (self.center_time / effective_duration) * 100
        
        # Formata o relatório
        report = f"--- Relatório do Teste Open Field ---\n\n"
        report += f"ID do Animal: {self.animal_id}\n"
        report += f"Data/Hora: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Duração Programada do Teste: {self.test_duration} segundos\n"
        report += f"Duração Efetiva do Teste: {effective_duration:.2f} segundos\n\n"
        report += f"Tempo Acumulado nas Áreas:\n"
        report += f"  Canto: {self.corner_time:.2f} segundos ({corner_percent:.2f}%)\n"
        report += f"  Lateral: {self.lateral_time:.2f} segundos ({lateral_percent:.2f}%)\n"
        report += f"  Centro: {self.center_time:.2f} segundos ({center_percent:.2f}%)\n\n"
        
        self.report_text.text = report
        
        # Armazena os dados para o gráfico
        self.test_data = {
            "ID do Animal": self.animal_id,
            "Data/Hora": time.strftime("%Y-%m-%d %H:%M:%S"),
            "Duração Programada (s)": self.test_duration,
            "Duração Efetiva (s)": effective_duration,
            "Tempo no Canto (s)": self.corner_time,
            "Porcentagem no Canto (%)": corner_percent,
            "Tempo na Lateral (s)": self.lateral_time,
            "Porcentagem na Lateral (%)": lateral_percent,
            "Tempo no Centro (s)": self.center_time,
            "Porcentagem no Centro (%)": center_percent,
        }
        
        # Gera o gráfico
        self.show_pie_chart()
    
    def show_pie_chart(self):
        # Limpa o container do gráfico
        self.chart_container.clear_widgets()
        
        labels = ['Canto', 'Lateral', 'Centro']
        sizes = [self.corner_time, self.lateral_time, self.center_time]
        colors = ['red', 'skyblue', 'forestgreen']
        
        # Remove áreas com tempo zero
        filtered_labels = []
        filtered_sizes = []
        filtered_colors = []
        
        for i, size in enumerate(sizes):
            if size > 0:
                filtered_sizes.append(size)
                filtered_labels.append(labels[i])
                filtered_colors.append(colors[i])
        
        if not filtered_sizes:
            no_data_label = Label(text="Nenhum tempo registrado para exibir o gráfico.")
            self.chart_container.add_widget(no_data_label)
            return
        
        # Cria o gráfico
        fig = plt.figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        
        wedges, texts, autotexts = ax.pie(
            filtered_sizes, 
            labels=filtered_labels, 
            colors=filtered_colors,
            autopct='%1.1f%%', 
            startangle=90, 
            pctdistance=0.85
        )
        
        # Ajusta o texto
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontsize(10)
        for text in texts:
            text.set_fontsize(10)
        
        ax.axis('equal')
        ax.set_title("Distribuição de Tempo por Área")
        
        # Adiciona o gráfico ao container
        canvas = FigureCanvasKivyAgg(fig)
        self.chart_container.add_widget(canvas)
        
        plt.close(fig)  # Fecha a figura para liberar memória
    
    def export_report(self, instance):
        if not self.test_data:
            self.show_popup("Nenhum Dado", "Nenhum relatório foi gerado para exportar.")
            return
        
        # Cria um popup para escolher o local do arquivo
        content = BoxLayout(orientation='vertical', spacing=10)
        
        # Input para o nome do arquivo
        filename_input = TextInput(
            text=f"relatorio_{self.animal_id}_{time.strftime('%Y%m%d_%H%M%S')}.txt",
            multiline=False,
            size_hint_y=None,
            height=40
        )
        content.add_widget(Label(text="Nome do arquivo:", size_hint_y=None, height=30))
        content.add_widget(filename_input)
        
        # Botões
        buttons_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=50)
        
        save_btn = Button(text="Salvar")
        cancel_btn = Button(text="Cancelar")
        
        buttons_layout.add_widget(save_btn)
        buttons_layout.add_widget(cancel_btn)
        content.add_widget(buttons_layout)
        
        popup = Popup(title="Exportar Relatório", content=content, size_hint=(0.8, 0.4))
        
        def save_file(instance):
            try:
                filename = filename_input.text.strip()
                if not filename:
                    filename = f"relatorio_{self.animal_id}_{time.strftime('%Y%m%d_%H%M%S')}.txt"
                
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(self.report_text.text)
                
                popup.dismiss()
                self.show_popup("Exportação Concluída", f"Relatório exportado com sucesso para: {filename}")
            except Exception as e:
                self.show_popup("Erro na Exportação", f"Ocorreu um erro ao exportar o relatório: {str(e)}")
        
        save_btn.bind(on_press=save_file)
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', spacing=10)
        content.add_widget(Label(text=message))
        
        close_btn = Button(text="OK", size_hint_y=None, height=50)
        content.add_widget(close_btn)
        
        popup = Popup(title=title, content=content, size_hint=(0.6, 0.4))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()


class OpenFieldTestApp(App):
    def build(self):
        return OpenFieldApp()


if __name__ == "__main__":
    OpenFieldTestApp().run()