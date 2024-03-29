import numpy as np
import matplotlib as mp
import timeit

from fractions import Fraction

saida_2 = True

# Testando para ver se tem ou nao o modulo
try:
    from tabulate import tabulate as tb
except ImportError:
    saida_2 = False

class Problema:
    PRIMAL = 1
    DUAL = -1

class Sinal:
    MAIOR_IGUAL = 1
    IGUAL = 0
    MENOR_IGUAL = -1

class Tipo:
    MAX = 1
    MIN = -1

class Simplex:
    # Localizacao no array do tipo de restricao e o tipo de otimizacao
    __TIPO_RESTRICAO = 0

    # Digitos significativos para usar na precisao das saidas
    __DIGITOS_SIGNIFICATIVOS = 3

    # Total de numero de variaveis
    __numero_variavel = 0

    def __init__(self, tipo_fo, obj, orientacao_problema=Problema.PRIMAL):
        # Funcao objetivo
        self.obj = [tipo_fo] + obj + [0]

        # Colunas / Restricoes
        self.rows = []

        # Variaveis de folga
        self.__folga = []

        # Variaveis artificiais
        self.__art = []

        # z_0 para funcao objetivo artificial
        self.__z_0 = []

        # base
        self.base = []

        # Orientacao do Problema
        self.orientacao_problema = orientacao_problema

        self.__dual = [self.obj]

        self.__ordem_variaveis = {}

    def arredondar(self, valor):
        # Se for passado um objeto interavel, como uma lista
        if hasattr(valor, '__iter__') is True:
            frac = lambda x: str(Fraction(x).limit_denominator(10**self.__DIGITOS_SIGNIFICATIVOS))

            for idx in range(len(valor)):
                res = valor[idx]

                if hasattr(res, '__iter__') is True:
                    valor[idx] = map(frac, res)
                else:
                    raise TypeError('So eh aceito vetor de 2 dimensoes ou numero.')

        # Se for passado apenas um valor
        else:
            valor = np.round(valor, self.__DIGITOS_SIGNIFICATIVOS)

        return valor

    # Adicionando a lista de restricoes a tabela
    def adicionar_restricao(self, sinal, expressao, valor):
        # Primeiro vamos concatena-la
        self.rows.append([sinal] + expressao + [valor])
        self.__dual.append([sinal] + expressao + [valor])

    # Mudando para a forma padrao
    def __forma_padrao(self):
        print('\na)Mudando a funcao objetivo, se necessario')
        # Transforma a funcao MAX para MIN
        if self.obj[self.__TIPO_RESTRICAO] == Tipo.MAX:
            # numpy.dot converte para ndarray, entao
            # tolist() volta obj a ser um array
            self.obj = np.dot(self.obj, -1).tolist()
            self.obj = self.obj
            self.obj[self.__TIPO_RESTRICAO] = Tipo.MIN
        else:
            print('\nNao sera necessario mudar a funcao objetivo\n')

        self.mostrar_situacao()

        # Index do numero atual da variavel adicional
        # Deve ser decrescido -1 pois no inicio tem
        # o tipo da otimizacao MAX ou MIN e ainda
        # nao esta concatenado com rhs (valores)
        self.__numero_variavel = len(self.obj) - 2

        print('b)Vamos criar um base inicial:\n')

        # Transforma as desiguadades em igualdades
        for idx in range(len(self.rows)):
            self.__numero_variavel += 1

            # Caso tenha numero negativo do lado direito
            if self.rows[idx][-1] < 0:
                print('Precisamos multiplicar por -1 a restricao ' + str(idx+1) + '.')
                self.rows[idx] = np.dot(self.rows[idx], -1).tolist()

            sinal = self.rows[idx][self.__TIPO_RESTRICAO]

            # No caso se for igual, entao aplicamos as variaveis
            # artificiais
            if sinal == Sinal.IGUAL:
                print('Adicioando na restricao ' + str(idx+1) + ' a variavel' + \
                'x' +  str(self.__numero_variavel) + ' como variavel artificial.')

                self.__art += [self.__numero_variavel]
                print('Colocando ' + 'x' + str(self.__numero_variavel) + ' na base.\n')
                self.base.append(self.__numero_variavel)
                self.obj[-1:-1] = [0]

                # Adicionando zero as restricoes
                for row in self.rows:
                    row[-1:-1] = [0]

                # Adicionando coeficiente a restricao
                self.rows[idx][-2] = 1
            # No caso de for menor ou igual, ou seja, uma fase
            elif sinal == Sinal.MENOR_IGUAL:
                print('Adicionando na restricao ' + str(idx+1) + ' a variavel' + \
                'x' +  str(self.__numero_variavel) + ' como variavel de folga.')

                self.__folga += [self.__numero_variavel]
                self.obj[-1:-1] = [0]

                # Adicionando zero as restricoes
                for res in self.rows:
                    res[-1:-1] = [0]

                # Adicionando coeficiente a restricao
                self.rows[idx][-2] = 1

                # Colocando esse numero na base
                print('Colocando x' + str(self.__numero_variavel) + ' na base.\n')
                self.base.append(self.__numero_variavel)

                self.rows[idx][self.__TIPO_RESTRICAO] = Sinal.IGUAL

            # No caso de for maior ou igual, ou seja, de duas fases
            elif sinal == Sinal.MAIOR_IGUAL:
                print('Adicionando na restricao ' + str(idx+1) + ' a variavel' + \
                'x' +  str(self.__numero_variavel) + ' como variavel de folga.')

                print('Adicionando na restricao ' + str(idx+1) + ' a variavel' + \
                'x' +  str(self.__numero_variavel + 1) + ' como variavel artificial.')

                self.__folga += [self.__numero_variavel]
                self.__art += [self.__numero_variavel + 1]

                # Adicionando a variavel artificial a base
                print('Colocando x' + str(self.__numero_variavel + 1) + ' na base.\n')
                self.base.append(self.__numero_variavel + 1)

                # Como a cada interacao ele ja incrementa
                # eu aumento soh mais uma porque sao duas variaveis
                self.__numero_variavel += 1

                # Adicionando dois zeros a funcao objetivo
                self.obj[-1:-1] = [0, 0]

                for res in self.rows:
                    res[-1:-1] = [0, 0]

                self.rows[idx][-3] = -1
                self.rows[idx][-2] = 1
                self.rows[idx][self.__TIPO_RESTRICAO] = Sinal.IGUAL

    # saida normal sem nenhum modulo adicional
    def saida_1(self, orientacao_problema, tipo, obj):
        print('\n', orientacao_problema, tipo, '\t', self.arredondar(obj[0][1:]))
        for i in range(len(obj)-1):
            print('\t', self.arredondar(obj[i][1:]))
        for row in self.rows:
            print('\t', self.arredondar(row[1:]))

    # Tabela adicional que mostra a situacao dos sinais
    def saida_2_desigualdades(self, obj, rows):
        pretty_sinal = ['-' for a in range(len(obj))]
        for row in rows:
            analise = row[0]

            if analise == Sinal.IGUAL:
                pretty_sinal.append('=')
            elif analise == Sinal.MAIOR_IGUAL:
                pretty_sinal.append('>=')
            elif analise == Sinal.MENOR_IGUAL:
                pretty_sinal.append('<=')

        cabeca = ['Z'] + ['Z_0' for a in range(len(obj)-1)] + \
        ['R' + str(a) for a in range(1, len(pretty_sinal))]

        pretty_sinal = np.reshape(pretty_sinal, (1, -1))

        print('Sinais:\n' + tb(pretty_sinal, tablefmt='psql', headers=cabeca) + '\n')

    # saida com o tabulate, um modulo para a saida ficar legivel no terminal
    def saida_2(self, orientacao_problema, tipo, obj):
        pretty_row = []
        for row in self.rows:
            pretty_row.append(row[1:])

        pretty_obj = []
        for fo in obj:
            pretty_obj.append(fo[1:])

        pretty_order = ''

        if len(self.__ordem_variaveis) != 0:
            if self.__numero_variavel > len(self.__ordem_variaveis):
                self.__ordem_variaveis = {q:q+1 for q in range(self.__numero_variavel)}

            pretty_order = ['x' + str(a) for a in self.__ordem_variaveis.values()]
        else:
            tamanho_obj = len(obj[0][1:-1])
            self.__ordem_variaveis = {x: x+1 for x in range(tamanho_obj)}
            pretty_order = ['x' + str(a) for a in self.__ordem_variaveis.values()]


        # orientacao + tipo + tabela + formato da tabela + headers
        print('\n' + str(orientacao_problema) + ' ' + str(tipo) + '\n' +\
        tb(self.arredondar(pretty_obj + pretty_row),\
        tablefmt='psql',\
        headers=pretty_order+['rhs']) + '\n')

        self.saida_2_desigualdades(obj, self.rows)

    # Mostra a situacao atual da matriz
    def mostrar_situacao(self, pack=[], funcao_objetivo_original=True):

        if funcao_objetivo_original is True:
            pack = [self.obj]
        else:
            pack = [pack.tolist()] + [self.obj]

        tipo = ''
        tipo_otimizacao = pack[0][self.__TIPO_RESTRICAO]

        if tipo_otimizacao == Tipo.MIN:
            tipo = 'min'
        elif tipo_otimizacao == Tipo.MAX:
            tipo = 'max'
        else:
            print('Linha objetivo ' + str(self.obj))
            raise ValueError('Erro no tipo da linha objetivo.')

        orientacao = ''
        orientacao_problema = self.orientacao_problema

        if orientacao_problema == Problema.PRIMAL:
            orientacao = '(P)'
        elif orientacao_problema == Problema.DUAL:
            orientacao = '(D)'
        else:
            print('Numero da orientacao problema: ' + str(self.orientacao_problema))
            raise ValueError('Erro na orientacao do problema.')

        if saida_2 is False:
            self.saida_1(orientacao, tipo, pack)
        else:
            self.saida_2(orientacao, tipo, pack)

    # Procura pelo pivo
    def __pivo(self, obj, base=False):
        # Mostrando a base atual
        print('\nBase atual ' + str(self.base))

        # Variavel flag
        menor = float('Infinity')

        objetivo = obj.tolist()

        # Index inicial para escolher quem entra na base
        entra_base = -1

        # Index inicial para escolher quem sai da base
        sai_base = -1

        # Caso eu tenha repassado uma base especial
        if base is False:
            # Encontra o indice da coluna com o valor mais negativo
            # na funcao objetivo  para saber quem entra na base
            vitima = [a for a in objetivo[1:-1] if a < 0]

            if len(vitima) > 0:
                entra_base = objetivo[1:-1].index(min(vitima)) + 1
                print('\nNa funcao objetivo,\nesse eh o menor numero negativo: ' + \
                str(self.arredondar(obj[entra_base])) + ' [coluna=' + str(entra_base) + ']')
            # Caso nao haja ninguem para entrar na base,
            # entao estamos na solucao otima
            else:
                print('ja esta na solucao otima')

        # Caso eu precise eliminar as variaveis artificiais da base
        else:
            # pegando o menor o indice das variaveis artificiais
            sai_base = min([a for a in self.base for b in self.__art if a == b])

            # Indice da variavel artificial na base para saber a linha do pivo
            idx = self.base.index(sai_base)

            # Real indice no dicionario ou seja, real coluna no pivo no dicionario
            idx_aux = {a:b for a, b in self.__ordem_variaveis.items() if b == sai_base}
            idx_aux = [a for a in idx_aux][0]

            # Teste para ver se a variavel artificial funciona
            if self.rows[idx][idx_aux] == 0:
                possiveis_entradas = {a:b for a, b in self.__ordem_variaveis.items()\
                for c in self.__art if b is not c}
                possiveis_entradas = min(possiveis_entradas.values())
                entra_base = possiveis_entradas


        if entra_base != -1:
            print('\nEsse que entra: x' + str(entra_base) + '\n')
            # Vamos procurar quem sai da base
            for index, restricao in enumerate(self.rows):
                # Exclui divisoes por zero
                if restricao[entra_base] > 0:
                    # Divisao entre o resultado da restricao
                    # e a vitima para ser o pivo
                    razao = self.arredondar(restricao[-1] / float(restricao[entra_base]))
                    print('Na restricao ' + str(index+1) + ', com base x' + \
                    str(self.base[index]) + ', a razao de ' + \
                    str(self.arredondar(restricao[-1])) + '/' + \
                    str(self.arredondar(restricao[entra_base])) + ' = ' + str(razao))

                    # Elimina numeros negativos da escolha do pivo
                    if razao < 0:
                        continue
                    elif razao < menor:
                        menor = razao
                        sai_base = index
                else:
                    print('Na restricao ' + str(index+1) + ', com base x' + \
                    str(self.base[index]) + ', o numero eh nulo, negativo ou indeterminado: ' + \
                    str(self.arredondar(restricao[-1])) + '/' + \
                    str(self.arredondar(restricao[entra_base])))
            if menor == float('Infinity'):
                print('\nproblema eh inviavel')
            else:
                print('\nEsse que sai: x' + str(self.base[sai_base]) + '\n')

        return entra_base, sai_base

    # Aqui vai procurar o pivo e fazer os escalonamentos necessarios
    def __escalonamento(self, obj=[], base=False):
        print('\n4)Procurando o pivo')
        funcao_objetivo_original = True

        if len(obj) in (0, 1):
            if len(obj) == 1:
                funcao_objetivo_original = False
            obj += [self.obj]
        else:
            print('\nValor de obj', obj)
            raise ValueError('Erro na passagem do parametro obj')

        criterio_parada = len([a for a in obj[0][1:-1] if a < 0]) or\
        len([x for x in self.base for y in self.__art if x == y])


        if criterio_parada != 0:
            # Alterando array para ndarray para fazer com que
            # cada linha seja do tipo float
            for i in range(len(obj)):
                obj[i] = np.array(obj[i], dtype=float)
            for restricao in self.rows:
                restricao = np.array(restricao, dtype=float)

            contador = 1
            while criterio_parada != 0:
                print('\n--------\n' + str(contador) + 'a Interacao com pivo')
                contador += 1

                entra_base, sai_base = self.__pivo(obj[0], base)

                # Significa que nao foi possivel achar um novo pivo
                if entra_base == -1 or sai_base == -1:
                    break

                # O pivo esta aqui
                pivo = float(self.rows[sai_base][entra_base])

                print('O pivo dessa interacao eh: ' + str(self.arredondar(pivo)) + \
                ' [linha=' + str(sai_base + 1) + ', coluna=' + str(entra_base) + ']\n')

                print('a)Dividindo a coluna pivo')
                # Agora vamos dividir a linha toda pelo proprio pivo
                self.rows[sai_base] = np.dot(self.rows[sai_base], 1 / pivo)

                self.mostrar_situacao(obj[0], funcao_objetivo_original)

                # Agora precisamos zerar a coluna do pivo nas restricoes
                # e depois na funcao objetivo
                print('\nb)Vamos zerar a coluna do pivo\n')

                linha_pivo = self.rows[sai_base]

                for i in range(len(self.rows)):
                    restricao = self.rows[i]
                    if i != sai_base:
                        self.rows[i] += np.dot(linha_pivo, -restricao[entra_base])
                        print('\nSomando a restricao ' + str(i + 1))
                        self.mostrar_situacao(obj[0], funcao_objetivo_original)

                print('\nSomando a linha do pivo a funcao objetivo')
                # Adicionando a linha pivo na funcao objetivo
                linha_pivo = linha_pivo[1:]

                # print 'Mostrando a soma da(s) fo(s)', obj
                for i in range(len(obj)):
                    obj[i][1:] += np.dot(linha_pivo, -obj[i][entra_base])
                    # Como eu sempre coloco a funcao objetivo original na ultima
                    # posicao, tempos que atualizar direto na fonte (self.obj)
                    # pois na funcao objetivo ela soh esta como copia por valor
                    if i == len(obj)-1:
                        self.obj = obj[i]
                self.mostrar_situacao(obj[0], funcao_objetivo_original)

                # Trocando a base
                self.base[sai_base] = entra_base

                criterio_parada = len([a for a in obj[0][1:-1] if a < 0])
        # Caso eu nao tenha achado candidato
        else:
            print('\nJa estamos na solucao otima.')

        # Descobre se o prblema eh de uma ou duas fases
    def __teste_fases(self):
        # Se houver variavel artificial
        # Preciso fazer a primeira fase das duas
        # ja que a segunda fase eh o mesmo processo
        if len(self.__art) > 0:
            print('O problema eh de duas fases.')

            self.__z_0 = np.zeros(2 + self.__numero_variavel, dtype=float)
            self.__z_0[self.__TIPO_RESTRICAO] = Tipo.MIN
            print('Mostrando nova funcao objetivo:')
            for art in self.__art:
                self.__z_0[art] = 1

            self.mostrar_situacao(self.__z_0, funcao_objetivo_original=False)

            # Vamos procurar onde esta as restricoes
            # de cada variavel artificial
            for i in range(len(self.rows)):
                for art in self.__art:
                    if self.rows[i][art] == 1:
                        aux = self.rows[i]
                        aux = np.dot(aux, -1).tolist()
                        self.__z_0 += aux

            print('Alterando os valores em suas respectivas restricoes temos:')
            self.mostrar_situacao(self.__z_0, False)
            print('Agora vamos trabalhar com ela...')
            self.__escalonamento([self.__z_0])

            # Lista de variaveis artificias como base
            variaveis_art_basicas = [a for a in self.base for b in self.__art if a == b]

            print('Chegamos em uma solucao otima\npara a primeira fase com base: ' + \
            str(self.base) + '\n')

            # Caso haja, precisamos tentar elimina-las usando elas como sai_base
            if len(variaveis_art_basicas) != 0:
                print('Temos variaveis artificiais como base, precisamos elimina-las.')
                self.__escalonamento([self.__z_0], base=True)
            else:
                print('Nao ha variaveis artificiais como base, vamos continuar.\n\n'+\
                'E vamos eliminar as variaveis artificiais. ' + str(self.__art))

                # Removendo as variaveis artificiais
                self.__ordem_variaveis = {chave: valor\
                for chave, valor in self.__ordem_variaveis.items() if valor not in self.__art}

                self.obj = np.delete(self.obj, self.__art)

                for i in range(len(self.rows)):
                    self.rows[i] = np.delete(self.rows[i], self.__art)

                self.__numero_variavel -= len(self.__art)
                self.__art = []

            print('Agora vamos para a segunda fase.')
            self.mostrar_situacao()
            self.__escalonamento()
        else:
            print('\nO problema eh de uma fase.')
            self.__escalonamento()


    def resolver(self, dualidade=True):
        print('\n1)Antes de comecar')
        self.mostrar_situacao()

        print('\n2)Mudando as restricoes para a forma padrao\n')
        self.__forma_padrao()
        self.mostrar_situacao()

        print('\n3)Passo a passo para o metodo de duas fases\n')
        self.__teste_fases()

        print('\n5)Resolucao')
        print('\nZ = ' + str(self.obj[-1]))
        x = [[self.base[a], b[-1]] for a, b in enumerate(self.rows)]
        x.sort()
        for res in x:
            print('x' + str(res[0]) + ' = ' + str(res[1]))

        if dualidade is True:
            print('\n6)Problema Dual:')
            self.__problema_dual()
        else:
            print('\n---- FIM ----\n')

    def __problema_dual(self):
        # Dicionario para ajudar no texto
        text_orientacao = {Problema.PRIMAL: 'primal', Problema.DUAL: 'dual'}

        if self.orientacao_problema in text_orientacao.keys():
            orientacao = text_orientacao[self.orientacao_problema]
        else:
            print('Numero da orientacao ' + str(self.orientacao_problema))
            ValueError('Ha um problema na orientacao do problema.')

        print('\nEste eh o problema ' + orientacao + ' inicial:\n\n' + \
        tb(self.__dual, tablefmt='psql',\
        headers=['tp'] + ['x' + str(a + 1) for a in range(len(self.__dual[0])-2)] + ['rhs']))

        print('\nTranspondo as restricoes:')
        transposta = np.transpose([a[1:] for a in self.__dual[1:]]).tolist()
        print('\n' + tb(transposta, tablefmt='psql',\
        headers=['x' + str(a + 1) for a in range(len(transposta[0]))] + ['rhs']))

        # Funcao objetivo do novo problema
        dual_obj = [-self.__dual[0][0]] + transposta[-1]

        orientacao = text_orientacao[-self.orientacao_problema]

        print(  '\nFuncao objetivo ' + str(orientacao) + ': ' + str(dual_obj))

        # Esses que eram os coeficientes do primal
        # vao fazer parte do rhs do dual
        z_to_rhs = self.__dual[0][1:-1]
        print('Resultados do problema ' + str(orientacao) + ': ' + str(z_to_rhs))
        # Removendo a ultima linha
        # que vai ser a nova linha objetivo
        transposta = np.delete(transposta, -1, axis=0).tolist()
        # for i, tr in enumerate(transposta):
        print(transposta)
        for i in range(len(transposta)):
            transposta[i] = [Sinal.MAIOR_IGUAL] + transposta[i] + [z_to_rhs[i]]
        print(transposta)
        transposta.insert(0, dual_obj)
        print(tb(transposta, tablefmt='psql',\
        headers=['tp'] + ['x' + str(a) for a in range(len(transposta[-1]))] + ['rhs']))

        # Agora vamos resolver o Problema
        problema_dual = Simplex(transposta[0][0], transposta[0][1:], Problema.DUAL)
        for restricao in transposta[1:]:
            problema_dual.adicionar_restricao(restricao[0], restricao[1:-1], restricao[-1])
        problema_dual.resolver(dualidade=False)

def testes():
    # Problema de uma fase
    """
    max z = 2x + 3y + 2z
    sa
    2x + y + z <= 4
    x + 2y + z <= 7
    z          <= 5
    x,y,z >= 0
    """
    # tabela = Simplex(Tipo.MAX, [2, 3, 2])
    # tabela.adicionar_restricao(Sinal.MENOR_IGUAL, [2, 1, 1], 4)
    # tabela.adicionar_restricao(Sinal.MENOR_IGUAL, [1, 2, 1], 7)
    # tabela.adicionar_restricao(Sinal.MENOR_IGUAL, [0, 0, 1], 5)
    # tabela.resolver()

    # Problema de duas fases
    """
    max z = 6x1 - x2
    sa
    4x1 + x2    <= 21
    2x1 + 3x2   >= 13
    x1 - x2      = -1
    x1,x2 >= 0
    """
    tabela_duas_fases = Simplex(Tipo.MAX, [6, -1])
    tabela_duas_fases.adicionar_restricao(Sinal.MENOR_IGUAL, [4, 1], 21)
    tabela_duas_fases.adicionar_restricao(Sinal.MAIOR_IGUAL, [2, 3], 13)
    tabela_duas_fases.adicionar_restricao(Sinal.IGUAL, [1, -1], -1)
    tabela_duas_fases.resolver()
if __name__ == '__main__':

    num_testes = 1
    tempo = round(timeit.timeit(testes, number=num_testes), 2)
    print('\nTempo: ' + str(tempo) + 's em ' + str(num_testes) + ' teste(s).')
