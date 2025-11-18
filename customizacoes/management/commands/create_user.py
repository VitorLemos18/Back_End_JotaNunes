# customizacoes/management/commands/create_user.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from customizacoes.models import Usuario


class Command(BaseCommand):
    help = 'Cria um usuário no sistema (auth_user e USUARIO)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            required=True,
            help='Nome de usuário para login'
        )
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email do usuário'
        )
        parser.add_argument(
            '--password',
            type=str,
            required=True,
            help='Senha do usuário'
        )
        parser.add_argument(
            '--nome',
            type=str,
            help='Nome completo do usuário (para tabela USUARIO)'
        )
        parser.add_argument(
            '--cargo',
            type=str,
            help='Cargo do usuário (para tabela USUARIO)'
        )
        parser.add_argument(
            '--id-usuario',
            type=int,
            help='ID do usuário na tabela USUARIO (se não informado, será gerado automaticamente)'
        )
        parser.add_argument(
            '--superuser',
            action='store_true',
            help='Cria como superusuário (admin)'
        )
        parser.add_argument(
            '--staff',
            action='store_true',
            help='Cria como staff (pode acessar admin)'
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        nome = options.get('nome') or username
        cargo = options.get('cargo')
        id_usuario = options.get('id_usuario')
        is_superuser = options.get('superuser', False)
        is_staff = options.get('staff', False) or is_superuser

        # Verifica se o usuário já existe
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.ERROR(f'Usuário "{username}" já existe!')
            )
            return

        # Cria o usuário no auth_user (Django)
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_superuser=is_superuser,
                is_staff=is_staff
            )
            self.stdout.write(
                self.style.SUCCESS(f'✓ Usuário Django criado: {username} (ID: {user.id})')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao criar usuário Django: {str(e)}')
            )
            return

        # Cria o usuário na tabela USUARIO
        try:
            # Se não informou id_usuario, usa o ID do User do Django
            if id_usuario is None:
                id_usuario = user.id

            # Verifica se já existe um usuário com esse ID
            if Usuario.objects.filter(id_usuario=id_usuario).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f'Usuário com ID {id_usuario} já existe na tabela USUARIO. '
                        f'Usando o ID do Django ({user.id})...'
                    )
                )
                id_usuario = user.id

            usuario = Usuario.objects.create(
                id_usuario=id_usuario,
                nome=nome,
                email=email,
                cargo=cargo
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Usuário criado na tabela USUARIO: {nome} (ID: {id_usuario})'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f'Aviso: Erro ao criar usuário na tabela USUARIO: {str(e)}. '
                    f'Usuário Django foi criado com sucesso.'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Usuário criado com sucesso!\n'
                f'  Username: {username}\n'
                f'  Email: {email}\n'
                f'  Tipo: {"Superusuário" if is_superuser else "Usuário normal"}'
            )
        )





