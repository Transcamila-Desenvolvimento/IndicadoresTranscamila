import imaplib
import email
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from dashboard.models import CTe

class Command(BaseCommand):
    help = 'Importa CTEs de anexos XML - Versão Simplificada e Corrigida'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Iniciando importação de CTEs da Luft...')

        config = settings.CTE_EMAIL_CONFIG

        if not config.get('EMAIL_PASSWORD'):
            self.stdout.write(self.style.ERROR('❌ Senha de e-mail não configurada!'))
            return

        try:
            # Conexão IMAP
            mail = imaplib.IMAP4_SSL(config['IMAP_SERVER'], config['IMAP_PORT'])
            mail.login(config['EMAIL_ACCOUNT'], config['EMAIL_PASSWORD'])
            mail.select('inbox')

            # Busca e-mails não lidos
            search_criteria = '(UNSEEN FROM "tms@luftagro.com.br")'
            status, messages = mail.search(None, search_criteria)
            email_ids = messages[0].split()

            self.stdout.write(f'📧 {len(email_ids)} e-mails não lidos encontrados')

            total_importados = 0

            for eid in email_ids:
                try:
                    status, msg_data = mail.fetch(eid, '(RFC822)')
                    msg = email.message_from_bytes(msg_data[0][1])

                    xml_anexos = self.buscar_anexos_xml(msg)
                    
                    if xml_anexos:
                        self.stdout.write(f'📎 E-mail {eid.decode()} contém {len(xml_anexos)} anexo(s) XML')
                        
                        for nome_arquivo, xml_content in xml_anexos:
                            try:
                                self.stdout.write(f'🔍 Processando: {nome_arquivo}')
                                
                                # Extrai dados diretamente do XML
                                dados = self.extrair_dados_xml_simples(xml_content)
                                
                                if dados and dados.get('numero_cte'):
                                    if self.salvar_cte_simples(dados, xml_content):
                                        total_importados += 1
                                        self.stdout.write(self.style.SUCCESS(f'✅ CTE {dados["numero_cte"]} importado com sucesso'))
                                else:
                                    self.stdout.write(f'❌ Não foi possível extrair dados válidos do XML')
                                    
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f'❌ Erro no arquivo {nome_arquivo}: {str(e)}'))

                    mail.store(eid, '+FLAGS', '\\Seen')
                    self.stdout.write(f'✅ E-mail {eid.decode()} processado')

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Erro no e-mail {eid}: {str(e)}'))
                    try:
                        mail.store(eid, '+FLAGS', '\\Seen')
                    except:
                        pass

            mail.close()
            mail.logout()

            self.stdout.write(self.style.SUCCESS(f'🎉 Importação concluída: {total_importados} CTE(s) importado(s)'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro de conexão: {str(e)}'))

    def buscar_anexos_xml(self, msg):
        """Busca anexos XML"""
        xml_anexos = []

        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename and filename.lower().endswith('.xml'):
                        file_data = part.get_payload(decode=True)
                        if file_data:
                            try:
                                xml_content = file_data.decode('utf-8')
                            except UnicodeDecodeError:
                                try:
                                    xml_content = file_data.decode('latin-1')
                                except:
                                    xml_content = file_data.decode('utf-8', errors='ignore')
                            xml_anexos.append((filename, xml_content))

        return xml_anexos

    def extrair_dados_xml_simples(self, xml_content):
        """Extrai dados do XML de forma direta e robusta"""
        try:
            # Remove namespaces para simplificar
            xml_clean = re.sub(r'xmlns="[^"]+"', '', xml_content)
            root = ET.fromstring(xml_clean)
            
            # Encontra o elemento infCte independente da estrutura
            infCte = None
            if root.tag == 'cteProc':
                # Estrutura: cteProc -> CTe -> infCte
                cte_elem = root.find('.//CTe')
                if cte_elem is not None:
                    infCte = cte_elem.find('infCte')
            elif root.tag == 'CTe':
                # Estrutura direta: CTe -> infCte
                infCte = root.find('infCte')
            
            if infCte is None:
                self.stdout.write('❌ Elemento infCte não encontrado')
                return None

            dados = {}

            # Dados básicos do CTe
            ide = infCte.find('ide')
            if ide is not None:
                dados['numero_cte'] = self.get_text(ide, 'nCT')
                dados['serie_cte'] = self.get_text(ide, 'serie')
                dados['cidade_origem'] = self.get_text(ide, 'xMunIni')
                dados['uf_origem'] = self.get_text(ide, 'UFIni')
                dados['cidade_destino'] = self.get_text(ide, 'xMunFim')
                dados['uf_destino'] = self.get_text(ide, 'UFFim')

                # Data de emissão
                dh_emi = self.get_text(ide, 'dhEmi')
                if dh_emi:
                    try:
                        # Formata a data corretamente
                        if 'T' in dh_emi:
                            data_str = dh_emi.split('T')[0]
                            dados['data_emissao'] = datetime.strptime(data_str, '%Y-%m-%d')
                        else:
                            dados['data_emissao'] = datetime.now()
                    except:
                        dados['data_emissao'] = datetime.now()

            # Emitente
            emit = infCte.find('emit')
            if emit is not None:
                dados['nome_fantasia_emitente'] = self.get_text(emit, 'xFant')
                dados['cnpj_emitente'] = self.get_text(emit, 'CNPJ')
                dados['razao_social_emitente'] = self.get_text(emit, 'xNome')

            # Remetente
            rem = infCte.find('rem')
            if rem is not None:
                dados['remetente'] = self.get_text(rem, 'xNome')
                dados['cnpj_remetente'] = self.get_text(rem, 'CNPJ')

            # Destinatário
            dest = infCte.find('dest')
            if dest is not None:
                dados['destinatario'] = self.get_text(dest, 'xNome')
                dados['cnpj_destinatario'] = self.get_text(dest, 'CNPJ') or self.get_text(dest, 'CPF')

            # Tomador (quem paga o frete)
            dados.update(self.extrair_tomador_simples(infCte))

            # Valores do frete
            vPrest = infCte.find('vPrest')
            if vPrest is not None:
                vTPrest = self.get_text(vPrest, 'vTPrest')
                dados['valor_frete'] = float(vTPrest) if vTPrest else 0.0

                # Componentes do frete
                for comp in vPrest.findall('Comp'):
                    nome = self.get_text(comp, 'xNome')
                    valor = float(self.get_text(comp, 'vComp') or 0)
                    
                    if nome == 'FRETE_PESO':
                        dados['frete_peso'] = valor
                    elif nome == 'ADVALOREM':
                        dados['advalorem'] = valor
                    elif nome == 'PEDAGIO':
                        dados['pedagio'] = valor
                    elif nome == 'GRIS':
                        dados['gerenciamento_risco'] = valor
                    elif nome == 'OUTROS':
                        dados['outros_valores'] = valor

            # Informações da carga
            infCTeNorm = infCte.find('infCTeNorm')
            if infCTeNorm is not None:
                infCarga = infCTeNorm.find('infCarga')
                if infCarga is not None:
                    for infQ in infCarga.findall('infQ'):
                        tpMed = self.get_text(infQ, 'tpMed')
                        qCarga = self.get_text(infQ, 'qCarga')
                        if tpMed and qCarga:
                            if 'VOLUME' in tpMed.upper():
                                dados['volumes'] = int(float(qCarga))
                            elif 'PESO' in tpMed.upper():
                                dados['peso'] = float(qCarga)

            # Chave do CTe
            chave = infCte.get('Id', '')
            if chave:
                dados['chave_cte'] = chave.replace('CTe', '')
            else:
                # Tenta encontrar a chave no protocolo
                protCTe = root.find('.//protCTe')
                if protCTe is not None:
                    infProt = protCTe.find('infProt')
                    if infProt is not None:
                        dados['chave_cte'] = self.get_text(infProt, 'chCTe')

            # Log dos dados extraídos
            if dados.get('numero_cte'):
                self.stdout.write(f'📊 Dados extraídos - CTE: {dados["numero_cte"]}')
                self.stdout.write(f'📍 {dados.get("cidade_origem", "")} → {dados.get("cidade_destino", "")}')
                self.stdout.write(f'💰 Frete: R$ {dados.get("valor_frete", 0):.2f}')
            else:
                self.stdout.write('❌ Número do CTE não encontrado no XML')

            return dados

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao extrair dados XML: {str(e)}'))
            return None

    def extrair_tomador_simples(self, infCte):
        """Extrai dados do tomador de forma simplificada"""
        dados_tomador = {
            'tomador_razao_social': '',
            'tomador_cnpj': '',
            'tomador_tipo': ''
        }

        try:
            ide = infCte.find('ide')
            if ide is not None:
                # Verifica toma4 primeiro (tomador "Outros")
                toma4 = ide.find('toma4')
                if toma4 is not None:
                    dados_tomador['tomador_razao_social'] = self.get_text(toma4, 'xNome')
                    dados_tomador['tomador_cnpj'] = self.get_text(toma4, 'CNPJ')
                    dados_tomador['tomador_tipo'] = 'Outros'
                    return dados_tomador

                # Verifica o tomador normal
                toma = ide.find('toma')
                if toma is not None:
                    tipo_tomador = toma.text
                    if tipo_tomador == '0':  # Remetente
                        rem = infCte.find('rem')
                        if rem is not None:
                            dados_tomador['tomador_razao_social'] = self.get_text(rem, 'xNome')
                            dados_tomador['tomador_cnpj'] = self.get_text(rem, 'CNPJ')
                            dados_tomador['tomador_tipo'] = 'Remetente'
                    elif tipo_tomador == '1':  # Expedidor
                        exped = infCte.find('exped')
                        if exped is not None:
                            dados_tomador['tomador_razao_social'] = self.get_text(exped, 'xNome')
                            dados_tomador['tomador_cnpj'] = self.get_text(exped, 'CNPJ')
                            dados_tomador['tomador_tipo'] = 'Expedidor'
                    elif tipo_tomador == '3':  # Destinatário
                        dest = infCte.find('dest')
                        if dest is not None:
                            dados_tomador['tomador_razao_social'] = self.get_text(dest, 'xNome')
                            dados_tomador['tomador_cnpj'] = self.get_text(dest, 'CNPJ') or self.get_text(dest, 'CPF')
                            dados_tomador['tomador_tipo'] = 'Destinatário'

            # Se não encontrou, assume remetente
            if not dados_tomador['tomador_razao_social']:
                rem = infCte.find('rem')
                if rem is not None:
                    dados_tomador['tomador_razao_social'] = self.get_text(rem, 'xNome')
                    dados_tomador['tomador_cnpj'] = self.get_text(rem, 'CNPJ')
                    dados_tomador['tomador_tipo'] = 'Remetente'

        except Exception as e:
            self.stdout.write(f'⚠️ Erro ao identificar tomador: {str(e)}')

        return dados_tomador

    def get_text(self, element, tag):
        """Extrai texto de elemento XML de forma segura"""
        if element is None:
            return ''
        elem = element.find(tag)
        return elem.text if elem is not None else ''

    def salvar_cte_simples(self, dados, xml_content):
        """Salva o CTe de forma simplificada"""
        try:
            with transaction.atomic():
                # Verifica se já existe
                if CTe.objects.filter(numero_cte=dados['numero_cte']).exists():
                    self.stdout.write(self.style.WARNING(f'⚠️ CTE {dados["numero_cte"]} já existe'))
                    return False

                # Cria o CTe
                cte = CTe(
                    numero_cte=dados['numero_cte'],
                    serie_cte=dados.get('serie_cte', '1'),
                    chave_cte=dados.get('chave_cte', ''),
                    cidade_origem=dados.get('cidade_origem', ''),
                    uf_origem=dados.get('uf_origem', ''),
                    cidade_destino=dados.get('cidade_destino', ''),
                    uf_destino=dados.get('uf_destino', ''),
                    remetente=dados.get('remetente', ''),
                    cnpj_remetente=dados.get('cnpj_remetente', ''),
                    destinatario=dados.get('destinatario', ''),
                    cnpj_destinatario=dados.get('cnpj_destinatario', ''),
                    tomador_razao_social=dados.get('tomador_razao_social', ''),
                    tomador_cnpj=dados.get('tomador_cnpj', ''),
                    tomador_tipo=dados.get('tomador_tipo', ''),
                    nome_fantasia_emitente=dados.get('nome_fantasia_emitente', ''),
                    cnpj_emitente=dados.get('cnpj_emitente', ''),
                    razao_social_emitente=dados.get('razao_social_emitente', ''),
                    valor_frete=float(dados.get('valor_frete', 0)),
                    frete_peso=float(dados.get('frete_peso', 0)),
                    advalorem=float(dados.get('advalorem', 0)),
                    pedagio=float(dados.get('pedagio', 0)),
                    outros_valores=float(dados.get('outros_valores', 0)),
                    gerenciamento_risco=float(dados.get('gerenciamento_risco', 0)),
                    volumes=int(dados.get('volumes', 0)),
                    peso=float(dados.get('peso', 0)),
                    data_emissao=dados.get('data_emissao', datetime.now()),
                    arquivo_xml=xml_content
                )

                cte.save()

                # Log detalhado
                self.stdout.write(self.style.SUCCESS(f'✅ CTE {dados["numero_cte"]} salvo'))
                self.stdout.write(f'   🗺️  {dados.get("cidade_origem", "")}/{dados.get("uf_origem", "")} → {dados.get("cidade_destino", "")}/{dados.get("uf_destino", "")}')
                self.stdout.write(f'   💰 R$ {float(dados.get("valor_frete", 0)):.2f}')
                self.stdout.write(f'   📦 {dados.get("volumes", 0)} volumes | ⚖️ {dados.get("peso", 0):.0f} kg')
                
                if dados.get('tomador_razao_social'):
                    self.stdout.write(f'   👤 Tomador: {dados["tomador_razao_social"]}')

                return True

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao salvar CTE: {str(e)}'))
            return False