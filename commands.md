# Zestaw komend z opisem
1. !rupella lub /rupella - ukryta komenda nie podpowiadana przez discorda, blokuje ona dostęp do gier na zapleczu (easter egg)
2. [**ADMIN COMMAND**] /reset-rupella-status - wyczyszczenie blacklisty rupelli po tej komendzie gracze którzy są zablokowani przez rupelle (komenda 1) ponownie będa w stanie wykonywać akcje w oko
3. /cytat - losuje cytat elfiego uczonego 
4. [**ADMIN COMMAND**] /reset-bot-status {{VALUE}} - komenda do resetowania statusu botów. Boty jezeli nie mają włączonego ciągłego trybu gry, mogą zagrać z każdym użytkownikiem tylko 1 raz. Ta komenda służy do wyczyszczenia listy gracze, z którymi dany bot grał. Po jej wykonaniu gracze, którzy już raz zagrali z danym botem będą mogli ponownie wyzwać przeciwnika. Za wartość {{VALUE}} wstawiamy jedna z opcji:
   1. all - wyczyści statusy wszystkich botów
   2. amalberg - wyczyści statusy bota amalberg
   3. gerald - wyczyści statusy bota geralda
   4. guerino - wyczyści statusy bota guerino
   5. liebwin - wyczyści statusy bota liebwina
   6. talan - wyczyści statusy bota talan
   7. thrognik - wyczyści statusy bota thrognika
5. [**ADMIN COMMAND**] /get-oponents-of-bot {{VALUE}} - zwraca ID użytkowników z którymi dany bot grał (\n to znacznik nowej linni do zignorowania). Użytkownicy odzieleni są przecinkami. Za wartość {{VALUE}} wstawiamy jedna z opcji:
   1. amalberg - wyświetli id przeciników amalberg
   2. gerald - wyświetli id przeciników geralda
   3. guerino - wyświetli id przeciników guerino
   4. liebwin - wyświetli id przeciników liebwina
   5. talan - wyświetli id przeciników talan
   6. thrognik - wyświetli id przeciników thrognika
6. [**ADMIN COMMAND**] /clean-logs - czyści główny plik logów (**PRZED JEGO WYCZYSZCZENIEM UPEWNIJ SIE ŻE NA PEWNO CHCESZ TO ZROBIĆ I CZY MASZ POBRANE LOGI**). Ta komenda ma pomóc zaoszczędzić miejsce na serwerze i czyścić obsłużone już inforamcje o rozegranych rozgrywkach.
7. [**ADMIN COMMAND**] /kill-bastian - awaryjna komenda, która powinna zabić proces bota i go wyłączyć
8. [**ADMIN COMMAND**] /get-bot-full-logs - zwraca główny plik logów odnośnie rozegranych rozgrywek. Plik ma służyć weryfikacji wydarzen, obsłużeniu kwot, które postawiono i które należy przypisac odpisać graczom.
9. [**ADMIN COMMAND**] /get-bot-sumup-logs - zwraca sumupowy plik logów odnośnie rozegranych rozgrywek. Plik ma służyć obsłużeniu kwot, które postawiono i które należy przypisac odpisać graczom.
10. /oko-pomoc - wyświetla wszystkie komendy potrzebne do tego by zagrać w oko i się w nim odnaleźć
11. /oko-gracze - jako że z danym botem może grać tylko 1 osoba na raz komenda oko-gracze umożliwia podejrzeć, które z botów są aktualnie dostępne do wyzwania na pojedynek. Uwaga istnieje możliwośc zablokowania pernamentnego, któregoś z botów przez developera w config pliku.
12. /wyzwij-X - zestaw komend do wyzwania botów
    1. /wyzwij-thrognik - wyzwij thrognika do gry w oko, thrognik gra o kwoty między (25; 41)
    2. /wyzwij-talan - wyzwij talana do gry w oko, talan gra o sumy (30; 51)
    3. /wyzwij-guerino - wyzwij guerino do gry w oko, guerino gra o 1 miedziaka zawsze
    4. /wyzwij-liebwin - wyzwij liebwina do gry w oko, liebwin gra o kwotę (1;10)
    5. /wyzwij-gerald - wyzwij geralda do gry w oko, gerald gra o kwotę (9;26)
    6. /wyzwij-amalberg - wyzwij amalberg do gry w oko, amalberg gra o kwotę (19;30)
13. /dobieram-X - jeżeli jesteś z którymś z botów w grze, pisząc np. dobieram-thrognik dobierasz jedną kość do Twojej obecnej puli. Nie będąc w grze z danym botem komenda nie ma rekacji.
14. /rzucam-X - jeżeli jesteś z którymś z botów w grze, pisząc np. rzucam-thrognik rzucasz dostępną pulą kości. Nie będąc w grze z danym botem komenda nie ma reakcji.