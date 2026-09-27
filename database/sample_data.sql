-- =============================================================================
-- LIBRARY MANAGEMENT SYSTEM - REALISTIC SAMPLE DATA SEED
-- Exactly 50 Students (Roll 2417101 - 2417150), Passwords std101 - std150
-- Admin: admin / admin123
-- Database: library_db
-- =============================================================================

USE `library_db`;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE `fines`;
TRUNCATE TABLE `issued_books`;
TRUNCATE TABLE `book_authors`;
TRUNCATE TABLE `books`;
TRUNCATE TABLE `authors`;
TRUNCATE TABLE `categories`;
TRUNCATE TABLE `students`;
TRUNCATE TABLE `users`;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. USERS & ADMIN ACCOUNT
INSERT INTO `users` (`user_id`, `username`, `password_hash`, `role`, `created_at`) VALUES
(1, 'admin', 'scrypt:32768:8:1$0qjur1QqlfIUo51D$a79ba0c004ff10ed4d53ccf89706bf7838dfabc2dda3d0042edb6206ced1848467f0932060bd473c9104b4b7ae8c2951a598a5488a7ff5eb1912e415f92d79d9', 'ADMIN', NOW()),
(2, '2417101', 'scrypt:32768:8:1$vGuGNIRCv0AVNdf4$890c94239a5c42511f9d2df5ac4b7964c4260b9b99fc4fc4cc694717eabc0ca5c255aec36bc6582d9a8e88c9a901725a4c036e4d976dcf25481c5e07925bbdf5', 'STUDENT', NOW()),
(3, '2417102', 'scrypt:32768:8:1$VDCiFoppSSszFyEC$52610e4b073a58dc5dfb0cd79302026d4d7593e146177179229b684e558423086fce181d597a5abbab7fa1ad7200ab2c7df7fef33c3ad270379312324b993b2c', 'STUDENT', NOW()),
(4, '2417103', 'scrypt:32768:8:1$vlYfaqtOtTY9vmP6$246e5a2d77ef277412e9617f3d1c7f83b058dcf03f39181e49ef30ff4d7ba9113733e15abb09d6472271ef00b8906c8aa9f53acc8eaaa826436dc8715f21f630', 'STUDENT', NOW()),
(5, '2417104', 'scrypt:32768:8:1$IUxL4Mw3PiNe2DS6$351ed03318eb6125b706fa080495fd0c303be5754e00aca6ef0f10a1871ce32a688c8917ce05fbe7ad8c02b19eaa702652d695a96226bbfaf6ad1a885f8a8b39', 'STUDENT', NOW()),
(6, '2417105', 'scrypt:32768:8:1$h6NRu0WDOiP8MV5C$e51cbab78ce402374396e962a509baf70263d1801c7a2d7d81b4e88b5ae4c0db14a6a104fb7f19492e2037e4cb92407f22b91d2765b738e01a90b22d047408d9', 'STUDENT', NOW()),
(7, '2417106', 'scrypt:32768:8:1$f7j6rYCd9t89WmG8$8e5f8c41d792e039ff976e6cc3570928b1ac8c28360edf898429e0cce3f335709f2df730211e5ed765f16da3e6061dee502fe27e81e2419ba7793d532a016152', 'STUDENT', NOW()),
(8, '2417107', 'scrypt:32768:8:1$SvNev0RCEGEKzAoI$0959ee8d2333b85525c5ac1a1e5fb92b798c7c4402369588357d81d0862ee0ccae0f8d010be3410d9e9e600e6acdee339e5b2a5beed48123e2cd37cff60626ec', 'STUDENT', NOW()),
(9, '2417108', 'scrypt:32768:8:1$ywvgqoLcUg57ztHH$70f29ecc7ff943c1f0ad1137cb69753996670495d9805b83e592191722769fc80f7a6ff3d0e973bc4c374e7f4619cb368eb5efab73058162a64daa77e7ed8353', 'STUDENT', NOW()),
(10, '2417109', 'scrypt:32768:8:1$jx5Kswq6wPVX7V1c$257ed453edc2bce957bfe3173408710b540a71038cfa4fd7c345628c40a7a804c0195fa3f8bfd6d72ffc7ebcd2992efaee5e514531f5250b3d89598922d1a942', 'STUDENT', NOW()),
(11, '2417110', 'scrypt:32768:8:1$M7WmvkkQNvmkXULd$b58072e15599cf6686d9941da63237f4c7a486b1f4dd987fec5788c4754e2b6238d34ec3624f7e92009f719d264666f25f28f167963d21074d110234bc782adf', 'STUDENT', NOW()),
(12, '2417111', 'scrypt:32768:8:1$2Mzz6yqbKanS5LrV$43c68ff5c1ccb5f6665970f94f1ec13b83915830bcc15dd456327d1012cd33776f90bc8ccb1f5a41670794973f8295eaad606792a733a9978f4a81ca25d57440', 'STUDENT', NOW()),
(13, '2417112', 'scrypt:32768:8:1$ngCuFhN7i1c7OkGs$be577ca41d5c4f3d6bbe65a4dc565f94d02972ffc446b6084087c2412d160c4c52c590f8661ca9974093f32088e1f26382aca17655102913c02e02ce2629df5c', 'STUDENT', NOW()),
(14, '2417113', 'scrypt:32768:8:1$55jeM0DbLdiP0JZH$0b6869dbc0f6380ad4cce6bbe08c50cc367d159c18d8e83023d37c66e51bbc6a6c9adb6a9b100bb640f01c0cf25e7711e9fb88544aaf14408ed1de47dc0abc46', 'STUDENT', NOW()),
(15, '2417114', 'scrypt:32768:8:1$nJ8hHEa0xw67TlSI$071666af34102d77ce2cc4a5ab525f3f948a67b7da5a8b439f6330c087cb8ed593848690bfedbb0e8b9c3c6513c22b5c984d8686fc0fd99ec59555b46f77f390', 'STUDENT', NOW()),
(16, '2417115', 'scrypt:32768:8:1$zv0IimL2403jtiYO$7ae43ccfa30087844fa366d07ffe40a6e0ef66b659b4c99de11ee7f92b97a9da4c29bf5ac130287142a4f1698835dc2b8932f7a1b63bc52fb58dba49885feadb', 'STUDENT', NOW()),
(17, '2417116', 'scrypt:32768:8:1$NSUEMqLZYKIv9KHM$4d1c219fa6e48eba49e0966328953420f84b9fb57cd7890364a39270e3f8b95b23bb2f6818e8d39a2f8734396e7fb44ecb5ac45cf0c75f4096946b544273d5bb', 'STUDENT', NOW()),
(18, '2417117', 'scrypt:32768:8:1$iP3y22WbLAA5Q1PF$4801421582f7a338a97ea47380a5a3541fb5981f6f581398a3375393883e9c4a0a99949cbd5aaae52821cc6f9a0b6f814b133e9813471fbb102b6c0ebfbd07c3', 'STUDENT', NOW()),
(19, '2417118', 'scrypt:32768:8:1$qiqBxXFC0h7exeL0$b40d3af1196f6a3002455dab0cf0064c470bbcd3fea35f6e55857b05410ee50ef8ca361646d1dab9004c55c83ff7bb068ca31cffd7c2270ac84758c9f222707d', 'STUDENT', NOW()),
(20, '2417119', 'scrypt:32768:8:1$GKgj2kaIxviFd9uh$a79cf02936ed3f59b5eee07cd47ebf2a4b17207b0283da879e5ce2b45c6f4c7d136350043f6b4850b9cf049926a97a889579c2b8a91ed4ae2aab419dc2a0208d', 'STUDENT', NOW()),
(21, '2417120', 'scrypt:32768:8:1$O4r3pqfk5qSmiTZ9$ad488245a34a5efa5367acb17e503c907302077c79b9b7e3779328de79f229a476596f08861271ab71d1669d513af3b3285a403d9456ebfbd1e740d1d59e88a2', 'STUDENT', NOW()),
(22, '2417121', 'scrypt:32768:8:1$t6Wf9vYp8ddexe91$921b289dd61073b48e0fc18ad373ad3e7fe2d7c8c1f12d629496aea423081557833f17658b57590abf12d495c8548e963d2aa3bc047d5a5f50654682bd404d32', 'STUDENT', NOW()),
(23, '2417122', 'scrypt:32768:8:1$w1uPBf5oXLjoa6xL$3a9e5f6356782e2ae23429a1cff5c7d46f0b2223eb6d15f345e76a2184fe5577f49b4773eff3cd96425e9dd516dbf21d786bb3326f029e6233e9c79baf4fc073', 'STUDENT', NOW()),
(24, '2417123', 'scrypt:32768:8:1$iyG8CuiwfYouHVRW$1a6b23060d3b231a39a4bc7ca510cd6a90412df354b2a72e502f0e9c927f9d17a15709e8d6ab80b0407cf7923e5916601a74c7824248698ef87e6ee3d64256ea', 'STUDENT', NOW()),
(25, '2417124', 'scrypt:32768:8:1$lhLj7PMgFX5nb7gY$37684577b32f0197498d455e26228d30a35dd894bb31846545c40d243c5b5badf1d2d0cd8bc679949c1a0f751aeadecce87471b58997ef110d1a98e4f7b3744a', 'STUDENT', NOW()),
(26, '2417125', 'scrypt:32768:8:1$Gv91elAkmuXQ7ZPF$78429166ca0286253273f3bd8b70f2a37d904c59a7f924706a55803f5f319ce3127a61ab9e08665093ce995b8e4089d0fa8b793f568a07600cdc642a98b3b661', 'STUDENT', NOW()),
(27, '2417126', 'scrypt:32768:8:1$XrIEUa8WhvsxDnlO$f623e6411339b906e6ab687c5e73aedf3939a53cbf9e91498a064692aa16f6f5c84e13199053cb353f3ff03b6ca5f216b23343bcdbb5bfdb436bd865a5789d49', 'STUDENT', NOW()),
(28, '2417127', 'scrypt:32768:8:1$PxbNRTWMothIuDBd$1457ac0809311ac72249f3384ff7250962f72f14c873fc7f720846b9279879afeb1337a1438e520f0a6f3ce359f09f5c2480f895e1adf9c93e31af85c500357e', 'STUDENT', NOW()),
(29, '2417128', 'scrypt:32768:8:1$nmLpn5z4F6MWr1iQ$808393c350b4dd2d0b3aef5987fe1f87dc3c24214fda6702d2d7d35fd946ad317d215cd596995ab196db7a026f0009ede4ca4ce17e932976292b55b284dc147f', 'STUDENT', NOW()),
(30, '2417129', 'scrypt:32768:8:1$Mu3I08ITSX5fF5Um$651b0f8b10324d6458b3321cdd89ae6a95f40bea7b2f2bb4b29a110e9e6ad120787c25e36ee84301e404659ddff8ff061cc7de109b4ba4454dc878eb83704ce5', 'STUDENT', NOW()),
(31, '2417130', 'scrypt:32768:8:1$ipCc4UfC0bfqjC1n$e25ebac1304ac46ed1942504191a470ae347d9fcfc171eeced6be97e384838d907cae1f2eabfd975915b50d00591b36dbc82d8303b1c9cb9b156ffa1dcdef984', 'STUDENT', NOW()),
(32, '2417131', 'scrypt:32768:8:1$sGy3bdCfCDKen2bq$1e24fac6516926dae60a240c99c5fc357bfbbd49abc9475745716d6fe3fd6fb75f6f99b033f3103821c3e06b8f3c2c0014fd48369de793d8df5f10f511a0243d', 'STUDENT', NOW()),
(33, '2417132', 'scrypt:32768:8:1$9MrPTt8e6LZ8nrtA$5305fbf1db7df6e1a221c7b7d4c4c3324e915495820135201fc1420cdb6e2725037a98b9142eb05692c29bf22c9229ab165b73c2e008016dc199a1c43181fb38', 'STUDENT', NOW()),
(34, '2417133', 'scrypt:32768:8:1$xeLqZT45R1OYbcyq$71e20338ba0995771393b7f44ad7edb04dc56b914d586dde8034d7e3b06c41cb0d114c1ae1bf2abcb3e3980951af6f216f66e4d715b32682b871637522556718', 'STUDENT', NOW()),
(35, '2417134', 'scrypt:32768:8:1$4kVxMdYBtelTOSn6$ee9e1274f89c3cb2f1dea767bf2b9e85566f8b5e317ee6fc343ee9c0c12aeecdccfc9768a41a92da0a3e83b19c09ebb3d2a6a8f8f17ae7787410e6d836ee08a6', 'STUDENT', NOW()),
(36, '2417135', 'scrypt:32768:8:1$uVd8K4qJZ0tWfYVG$585d8cae0186add846f51b3c57ee59dd514b8eda49c4386c8b6b84d5e97c43aa0fdbec58929a1ab947ad8a7fc5081a400eb813a5ed35134df7dfe36021e3bdf4', 'STUDENT', NOW()),
(37, '2417136', 'scrypt:32768:8:1$fao4xSMZxgd2rU22$3bfb0f8246c12100f5f32affc08d49c7ecdf62728c64c9041e89e197169372a489e4bce51e96295288df1a319ad4770065369ea10b289aea7cbadbda3787715b', 'STUDENT', NOW()),
(38, '2417137', 'scrypt:32768:8:1$E6DXZoKI21tSGkti$0111ac1dcdf7e4a9384c4d0840f0f5286f308a7c9682ae706a250e38c205cc5f258e8dcc585759d7da7626659a41bf340836af48a74d90a3b9d4625d46a95534', 'STUDENT', NOW()),
(39, '2417138', 'scrypt:32768:8:1$dGZsMTKe560j4q6O$259f40cc81f34f2e49458ab2acb0f4d49b158d2d2ad9d8c8538c356a508dfe24f143f3f0a2ba1c5722282b51f990a0b1e75990cc35a31bd3471d80d870993245', 'STUDENT', NOW()),
(40, '2417139', 'scrypt:32768:8:1$FJujs6ACSyMzGKpv$a2ba528d8422868e73a8f2b3f9f7be0d9409dc8e27e29936068f1cf3f0d6b405dce87423725c959c301f5fb1657bf6cc6b05b17495ec3a273f65026f1e9784df', 'STUDENT', NOW()),
(41, '2417140', 'scrypt:32768:8:1$ddOD8d2WMkDZtZt2$248c5cce5246867657e5abc92c7f87c475ac8c5fdcdab713eacaea77a037f86e80e88c4464459cfdd092680d339a6133aabd6e53e887d7267fbc178a5d8dca33', 'STUDENT', NOW()),
(42, '2417141', 'scrypt:32768:8:1$fXe0MLnG6MD35TWm$6102388221aa2450fcc4424d2b08999dbe083ce148ef7786d4e7e92d079d815308e1734da0ee0f050252e85c373446f07c2d3bd3a0516dc2d7e9490e2be393f2', 'STUDENT', NOW()),
(43, '2417142', 'scrypt:32768:8:1$Ik652uJKU2iIkCtk$fc75a6ebc3673fcfe4a0126184c900b19c278de37eb56af56026e37fc0921b5b71fbc347c0f6473740e603cc3ac73bfe809ea1574b3ecc0db4635f4cc06009b8', 'STUDENT', NOW()),
(44, '2417143', 'scrypt:32768:8:1$joWDOgFhQCArvuYo$fd735a03a7accbb31e37381c41d71e4e6200c77c05010834213676d8f393d8cac72c7c463b48136c943366044a5e24a8ede307fa366930073bb861dcef1e5079', 'STUDENT', NOW()),
(45, '2417144', 'scrypt:32768:8:1$zOQuDC0DJjDQY3Rs$cba2161e3e867844e4ddb90d33996f4ad2120a4a820a9b368e0ed70728d62879ab91a158ed1f0b1b02264ac5b360bea7ea4b6e3e5d2d9b33c21fd1885357a7af', 'STUDENT', NOW()),
(46, '2417145', 'scrypt:32768:8:1$cKaBiruO3tykyf2R$e60737e296575e08f50275ab0307dcf21ee2433947c44c997aec7d028a1f6db952fa9bf9108ba33696ea5c0a56d444d4da3bb1d7c3eb3d41136c9b7e345c9ed9', 'STUDENT', NOW()),
(47, '2417146', 'scrypt:32768:8:1$kWM2qmchwYyPCn2g$56e6bea57772de1730798a2a1b257909061f1f5cc9f59bd8251d75ec025f2a4080228842850281266f2f7ac295ab4f5e122b4261b93a04eaa1c14bafddf057fa', 'STUDENT', NOW()),
(48, '2417147', 'scrypt:32768:8:1$kjFeGsJMqxDHyGCt$1fade36239e1a3048050b6f0e2b6b6c3b9f3b34cd461524c3e3175ae74d367e1c79298f8c9d1ae7e1ca1211b175679930074d8c186f0d68031f6719112f5013b', 'STUDENT', NOW()),
(49, '2417148', 'scrypt:32768:8:1$NxHAcztnqcIItkQv$f6004eb725184f1be20f9b7d43960ef98081786cddd1d8872603adaa2322c31fe902ebc5f578cb21f3df2bbda539c61ba6d0af8f04d58200225794677ce63056', 'STUDENT', NOW()),
(50, '2417149', 'scrypt:32768:8:1$uC6qx7D4xTVFYJcP$9c381c73b8d77d4caae61303dd18952efa4f32ad014eb3638b7fcd46a5fa72203198d665527c14dc24e6fdad13d66c2a2d95942449c015f55be72790db580d6c', 'STUDENT', NOW()),
(51, '2417150', 'scrypt:32768:8:1$z65HZdyNA6K8xAlz$d2ce694d92416fcad8a932cc6bc39acfbf4ca4aafe5986e93392dcb32ffc8798d852808e5e5008c35a43fba6eb9c85036e9d68346eb3416c350c653b2a389805', 'STUDENT', NOW());

-- 2. STUDENTS TABLE (50 STUDENTS)
INSERT INTO `students` (`student_id`, `user_id`, `roll_number`, `full_name`, `email`, `phone`, `department`, `borrowing_permission`, `created_at`) VALUES
(1, 2, '2417101', 'Aarav Sharma', 'aarav.sharma@college.edu', '9876543201', 'CSE', 'GRANTED', NOW()),
(2, 3, '2417102', 'Diya Patel', 'diya.patel@college.edu', '9876543202', 'IT', 'GRANTED', NOW()),
(3, 4, '2417103', 'Rohan Verma', 'rohan.verma@college.edu', '9876543203', 'ECE', 'GRANTED', NOW()),
(4, 5, '2417104', 'Ananya Iyer', 'ananya.iyer@college.edu', '9876543204', 'CSE', 'GRANTED', NOW()),
(5, 6, '2417105', 'Ishaan Gupta', 'ishaan.gupta@college.edu', '9876543205', 'ME', 'GRANTED', NOW()),
(6, 7, '2417106', 'Saanvi Nair', 'saanvi.nair@college.edu', '9876543206', 'IT', 'GRANTED', NOW()),
(7, 8, '2417107', 'Kabir Singh', 'kabir.singh@college.edu', '9876543207', 'CE', 'GRANTED', NOW()),
(8, 9, '2417108', 'Myra Joshi', 'myra.joshi@college.edu', '9876543208', 'CSE', 'GRANTED', NOW()),
(9, 10, '2417109', 'Arjun Reddy', 'arjun.reddy@college.edu', '9876543209', 'ECE', 'GRANTED', NOW()),
(10, 11, '2417110', 'Zara Khan', 'zara.khan@college.edu', '9876543210', 'IT', 'GRANTED', NOW()),
(11, 12, '2417111', 'Vihaan Rao', 'vihaan.rao@college.edu', '9876543211', 'ME', 'GRANTED', NOW()),
(12, 13, '2417112', 'Aditi Deshmukh', 'aditi.deshmukh@college.edu', '9876543212', 'CSE', 'GRANTED', NOW()),
(13, 14, '2417113', 'Reyansh Pillai', 'reyansh.pillai@college.edu', '9876543213', 'CE', 'GRANTED', NOW()),
(14, 15, '2417114', 'Prisha Kulkarni', 'prisha.kulkarni@college.edu', '9876543214', 'ECE', 'GRANTED', NOW()),
(15, 16, '2417115', 'Vivaan Chopra', 'vivaan.chopra@college.edu', '9876543215', 'IT', 'GRANTED', NOW()),
(16, 17, '2417116', 'Anvi Mehta', 'anvi.mehta@college.edu', '9876543216', 'CSE', 'GRANTED', NOW()),
(17, 18, '2417117', 'Aditya Sen', 'aditya.sen@college.edu', '9876543217', 'ME', 'GRANTED', NOW()),
(18, 19, '2417118', 'Sneha Roy', 'sneha.roy@college.edu', '9876543218', 'ECE', 'GRANTED', NOW()),
(19, 20, '2417119', 'Harshit Singla', 'harshit.singla@college.edu', '9876543219', 'CSE', 'GRANTED', NOW()),
(20, 21, '2417120', 'Pooja Hegde', 'pooja.hegde@college.edu', '9876543220', 'IT', 'GRANTED', NOW()),
(21, 22, '2417121', 'Aryan Bhatt', 'aryan.bhatt@college.edu', '9876543221', 'CE', 'GRANTED', NOW()),
(22, 23, '2417122', 'Kavya Menon', 'kavya.menon@college.edu', '9876543222', 'CSE', 'GRANTED', NOW()),
(23, 24, '2417123', 'Dhruv Mishra', 'dhruv.mishra@college.edu', '9876543223', 'ECE', 'GRANTED', NOW()),
(24, 25, '2417124', 'Riya Das', 'riya.das@college.edu', '9876543224', 'ME', 'GRANTED', NOW()),
(25, 26, '2417125', 'Manish Pandey', 'manish.pandey@college.edu', '9876543225', 'IT', 'REVOKED', NOW()),
(26, 27, '2417126', 'Tanya Bhatia', 'tanya.bhatia@college.edu', '9876543226', 'CSE', 'GRANTED', NOW()),
(27, 28, '2417127', 'Yashwant Goel', 'yashwant.goel@college.edu', '9876543227', 'CE', 'GRANTED', NOW()),
(28, 29, '2417128', 'Nisha Saxena', 'nisha.saxena@college.edu', '9876543228', 'ECE', 'GRANTED', NOW()),
(29, 30, '2417129', 'Tanmay Agarwal', 'tanmay.agarwal@college.edu', '9876543229', 'ME', 'GRANTED', NOW()),
(30, 31, '2417130', 'Deepak Verma', 'deepak.verma@college.edu', '9876543230', 'IT', 'GRANTED', NOW()),
(31, 32, '2417131', 'Bhavna Jain', 'bhavna.jain@college.edu', '9876543231', 'CSE', 'GRANTED', NOW()),
(32, 33, '2417132', 'Siddharth Kaul', 'siddharth.kaul@college.edu', '9876543232', 'ECE', 'GRANTED', NOW()),
(33, 34, '2417133', 'Gauri Somani', 'gauri.somani@college.edu', '9876543233', 'CE', 'GRANTED', NOW()),
(34, 35, '2417134', 'Naveen Tyagi', 'naveen.tyagi@college.edu', '9876543234', 'ME', 'GRANTED', NOW()),
(35, 36, '2417135', 'Meera Nambiar', 'meera.nambiar@college.edu', '9876543235', 'CSE', 'REVOKED', NOW()),
(36, 37, '2417136', 'Karan Malhotra', 'karan.malhotra@college.edu', '9876543236', 'IT', 'GRANTED', NOW()),
(37, 38, '2417137', 'Simran Gill', 'simran.gill@college.edu', '9876543237', 'ECE', 'GRANTED', NOW()),
(38, 39, '2417138', 'Gautam Bansal', 'gautam.bansal@college.edu', '9876543238', 'CE', 'GRANTED', NOW()),
(39, 40, '2417139', 'Pari Singhania', 'pari.singhania@college.edu', '9876543239', 'ME', 'GRANTED', NOW()),
(40, 41, '2417140', 'Rahul Tiwari', 'rahul.tiwari@college.edu', '9876543240', 'CSE', 'GRANTED', NOW()),
(41, 42, '2417141', 'Swati Dubey', 'swati.dubey@college.edu', '9876543241', 'IT', 'GRANTED', NOW()),
(42, 43, '2417142', 'Abhishek Yadav', 'abhishek.yadav@college.edu', '9876543242', 'ECE', 'GRANTED', NOW()),
(43, 44, '2417143', 'Komal Soni', 'komal.soni@college.edu', '9876543243', 'CE', 'GRANTED', NOW()),
(44, 45, '2417144', 'Sumit Chauhan', 'sumit.chauhan@college.edu', '9876543244', 'ME', 'GRANTED', NOW()),
(45, 46, '2417145', 'Ritika Sengupta', 'ritika.sengupta@college.edu', '9876543245', 'CSE', 'REVOKED', NOW()),
(46, 47, '2417146', 'Varun Chhabra', 'varun.chhabra@college.edu', '9876543246', 'IT', 'GRANTED', NOW()),
(47, 48, '2417147', 'Isha Bakshi', 'isha.bakshi@college.edu', '9876543247', 'ECE', 'GRANTED', NOW()),
(48, 49, '2417148', 'Alok Tripathi', 'alok.tripathi@college.edu', '9876543248', 'CE', 'GRANTED', NOW()),
(49, 50, '2417149', 'Divya Rastogi', 'divya.rastogi@college.edu', '9876543249', 'ME', 'GRANTED', NOW()),
(50, 51, '2417150', 'Chirag Sethi', 'chirag.sethi@college.edu', '9876543250', 'CSE', 'GRANTED', NOW());

-- 3. CATEGORIES TABLE
INSERT INTO `categories` (`category_id`, `category_name`, `description`) VALUES
(1, 'Database Systems', 'Relational databases, SQL, indexing, transaction processing, and query optimization'),
(2, 'Data Structures & Algorithms', 'Fundamental algorithms, data structures, complexity analysis, and computational theory'),
(3, 'Artificial Intelligence & ML', 'Machine learning, neural networks, deep learning, NLP, and intelligent agents'),
(4, 'Computer Networks', 'Network protocols, OSI reference model, TCP/IP, routing, and network security'),
(5, 'Operating Systems', 'Process scheduling, concurrency, virtual memory, file systems, and distributed OS'),
(6, 'Software Engineering', 'Agile methodologies, software architecture, design patterns, testing, and DevOps'),
(7, 'Mathematics & Theory', 'Discrete mathematics, linear algebra, graph theory, and probability for computer science'),
(8, 'Web Technologies', 'Full-stack development, modern frontend systems, backend services, and APIs');

-- 4. AUTHORS TABLE
INSERT INTO `authors` (`author_id`, `author_name`, `biography`) VALUES
(1, 'Abraham Silberschatz', 'Professor of Computer Science at Yale University; renowned for Database and OS textbooks.'),
(2, 'Henry F. Korth', 'Professor at Lehigh University; co-author of iconic Database System Concepts.'),
(3, 'S. Sudarshan', 'Professor of Computer Science at IIT Bombay; database systems researcher and author.'),
(4, 'Thomas H. Cormen', 'Professor of Computer Science at Dartmouth College; co-author of CLRS Introduction to Algorithms.'),
(5, 'Charles E. Leiserson', 'Professor of Computer Science at MIT; parallel computing and algorithms authority.'),
(6, 'Ronald L. Rivest', 'MIT Institute Professor, cryptographer, co-inventor of RSA algorithm.'),
(7, 'Clifford Stein', 'Professor of Industrial Engineering and Operations Research at Columbia University.'),
(8, 'Stuart Russell', 'Professor of Computer Science at UC Berkeley; AI pioneer.'),
(9, 'Peter Norvig', 'Director of Research at Google; co-author of AI: A Modern Approach.'),
(10, 'Andrew S. Tanenbaum', 'Professor Emeritus at Vrije Universiteit Amsterdam; MINIX creator and networking pioneer.'),
(11, 'David J. Wetherall', 'Networking researcher, professor at University of Washington and Google.'),
(12, 'Robert C. Martin', 'Renowned software craftsman affectionately known as ''Uncle Bob''; author of Clean Code.'),
(13, 'Erich Gamma', 'Software engineer and co-author of Design Patterns: Elements of Reusable Object-Oriented Software.'),
(14, 'Kenneth H. Rosen', 'Mathematician and computer scientist; author of Discrete Mathematics and Its Applications.'),
(15, 'Ian Goodfellow', 'Staff Research Scientist at Google Brain; pioneer of Generative Adversarial Networks (GANs).'),
(16, 'C.J. Date', 'Independent author, lecturer, and pioneer in relational database technology with E.F. Codd.');

-- 5. BOOKS TABLE (Reflecting accurate available_copies based on active loans)
INSERT INTO `books` (`book_id`, `isbn`, `title`, `category_id`, `total_copies`, `available_copies`, `edition`, `publish_year`) VALUES
(1, '9780078022159', 'Database System Concepts', 1, 6, 5, '7th Edition', 2019),
(2, '9780133970777', 'Fundamentals of Database Systems', 1, 5, 4, '7th Edition', 2016),
(3, '9780321197849', 'An Introduction to Database Systems', 1, 4, 4, '8th Edition', 2003),
(4, '9780262033848', 'Introduction to Algorithms (CLRS)', 2, 8, 6, '3rd Edition', 2009),
(5, '9780134685991', 'Algorithms', 2, 5, 5, '4th Edition', 2011),
(6, '9780321573513', 'Algorithms in a Nutshell', 2, 4, 4, '2nd Edition', 2016),
(7, '9780136042594', 'Artificial Intelligence: A Modern Approach', 3, 6, 5, '4th Edition', 2020),
(8, '9780262035613', 'Deep Learning', 3, 5, 4, '1st Edition', 2016),
(9, '9781491957660', 'Hands-On Machine Learning with Scikit-Learn', 3, 5, 5, '2nd Edition', 2019),
(10, '9780132126953', 'Computer Networks', 4, 6, 5, '5th Edition', 2010),
(11, '9780133594140', 'Data and Computer Communications', 4, 4, 4, '10th Edition', 2013),
(12, '9780131365483', 'TCP/IP Illustrated, Volume 1', 4, 4, 4, '2nd Edition', 2011),
(13, '9781119456339', 'Operating System Concepts (Dinosaur Book)', 5, 7, 6, '10th Edition', 2018),
(14, '9780133591620', 'Modern Operating Systems', 5, 5, 4, '4th Edition', 2014),
(15, '9780131429383', 'Operating Systems: Three Easy Pieces', 5, 4, 4, '1st Edition', 2018),
(16, '9780132350884', 'Clean Code: A Handbook of Agile Software Craftsmanship', 6, 6, 5, '1st Edition', 2008),
(17, '9780201633610', 'Design Patterns: Elements of Reusable Object-Oriented Software', 6, 5, 5, '1st Edition', 1994),
(18, '9780134494166', 'Clean Architecture', 6, 4, 4, '1st Edition', 2017),
(19, '9780073383095', 'Discrete Mathematics and Its Applications', 7, 6, 5, '8th Edition', 2018),
(20, '9780201896831', 'The Art of Computer Programming, Vol 1', 7, 3, 3, '3rd Edition', 1997),
(21, '9781491950357', 'Designing Data-Intensive Applications', 1, 6, 5, '1st Edition', 2017),
(22, '9781449373320', 'Learning SQL', 1, 5, 5, '3rd Edition', 2020),
(23, '9780596007126', 'Head First Design Patterns', 6, 5, 5, '2nd Edition', 2020),
(24, '9781491918890', 'JavaScript: The Definitive Guide', 8, 5, 4, '7th Edition', 2020),
(25, '9781593279509', 'Eloquent JavaScript', 8, 4, 4, '3rd Edition', 2018),
(26, '9781492051725', 'Learning Web Design', 8, 4, 4, '5th Edition', 2018),
(27, '9781492078838', 'Fluent Python', 8, 5, 5, '2nd Edition', 2022),
(28, '9781119293460', 'Pattern Recognition and Machine Learning', 3, 4, 4, '1st Edition', 2006),
(29, '9780262035453', 'Reinforcement Learning: An Introduction', 3, 4, 4, '2nd Edition', 2018),
(30, '9780134685992', 'Computer Organization and Architecture', 4, 5, 5, '11th Edition', 2018),
(31, '9780132143011', 'Compilers: Principles, Techniques, and Tools (Dragon Book)', 2, 4, 4, '2nd Edition', 2006),
(32, '9780262033855', 'Introduction to the Theory of Computation', 7, 5, 5, '3rd Edition', 2012),
(33, '9780132350891', 'The Pragmatic Programmer', 6, 5, 5, '20th Anniversary', 2019),
(34, '9781491954249', 'Building Microservices', 6, 4, 4, '2nd Edition', 2021),
(35, '9780134093413', 'Operating Systems: Internals and Design Principles', 5, 5, 5, '9th Edition', 2017);

-- 6. BOOK_AUTHORS JUNCTION TABLE
INSERT INTO `book_authors` (`book_id`, `author_id`) VALUES
(1, 1),
(1, 2),
(1, 3),
(2, 1),
(3, 16),
(4, 4),
(4, 5),
(4, 6),
(4, 7),
(5, 4),
(6, 4),
(7, 8),
(7, 9),
(8, 15),
(9, 8),
(10, 10),
(10, 11),
(11, 10),
(12, 10),
(13, 1),
(13, 2),
(14, 10),
(15, 1),
(16, 12),
(17, 13),
(18, 12),
(19, 14),
(20, 14),
(21, 3),
(22, 16),
(23, 12),
(24, 13),
(25, 12),
(26, 13),
(27, 8),
(28, 9),
(29, 8),
(30, 10),
(31, 4),
(32, 14),
(33, 12),
(34, 12),
(35, 1);

-- 7. ISSUED_BOOKS (Active Loans, Overdue Loans, and Historical Returns)
INSERT INTO `issued_books` (`issue_id`, `student_id`, `book_id`, `issue_date`, `due_date`, `return_date`, `status`, `remarks`) VALUES
(1, 12, 1, '2026-09-22', '2026-10-06', NULL, 'ISSUED', 'Standard library checkout'),
(2, 12, 4, '2026-09-19', '2026-10-03', NULL, 'ISSUED', 'Standard library checkout'),
(3, 12, 13, '2026-09-25', '2026-10-09', NULL, 'ISSUED', 'Standard library checkout'),
(4, 10, 7, '2026-09-23', '2026-10-07', NULL, 'ISSUED', 'Standard library checkout'),
(5, 10, 10, '2026-09-24', '2026-10-08', NULL, 'ISSUED', 'Standard library checkout'),
(6, 18, 16, '2026-09-21', '2026-10-05', NULL, 'ISSUED', 'Standard library checkout'),
(7, 18, 19, '2026-09-26', '2026-10-10', NULL, 'ISSUED', 'Standard library checkout'),
(8, 5, 2, '2026-09-20', '2026-10-04', NULL, 'ISSUED', 'Standard library checkout'),
(9, 19, 4, '2026-09-23', '2026-10-07', NULL, 'ISSUED', 'Standard library checkout'),
(10, 9, 8, '2026-09-07', '2026-09-21', NULL, 'OVERDUE', 'Standard library checkout'),
(11, 15, 14, '2026-09-09', '2026-09-23', NULL, 'OVERDUE', 'Standard library checkout'),
(12, 22, 21, '2026-09-24', '2026-10-08', NULL, 'ISSUED', 'Standard library checkout'),
(13, 26, 24, '2026-09-25', '2026-10-09', NULL, 'ISSUED', 'Standard library checkout'),
(14, 1, 1, '2026-08-18', '2026-09-01', '2026-08-30', 'RETURNED', 'Returned and verified'),
(15, 2, 4, '2026-08-23', '2026-09-06', '2026-09-07', 'RETURNED', 'Returned and verified'),
(16, 3, 7, '2026-08-08', '2026-08-22', '2026-08-22', 'RETURNED', 'Returned and verified'),
(17, 4, 10, '2026-08-13', '2026-08-27', '2026-08-28', 'RETURNED', 'Returned and verified'),
(18, 6, 13, '2026-07-29', '2026-08-12', '2026-08-14', 'RETURNED', 'Returned and verified'),
(19, 7, 16, '2026-08-28', '2026-09-11', '2026-09-12', 'RETURNED', 'Returned and verified'),
(20, 8, 19, '2026-09-02', '2026-09-16', '2026-09-16', 'RETURNED', 'Returned and verified'),
(21, 11, 21, '2026-08-18', '2026-09-01', '2026-09-01', 'RETURNED', 'Returned and verified'),
(22, 30, 1, '2026-08-23', '2026-09-06', '2026-09-13', 'RETURNED', 'Returned and verified'),
(23, 40, 4, '2026-08-28', '2026-09-11', '2026-09-15', 'RETURNED', 'Returned and verified');

-- 8. FINES TABLE (Penalties from late returns)
INSERT INTO `fines` (`fine_id`, `issue_id`, `student_id`, `fine_amount`, `payment_status`, `paid_date`) VALUES
(1, 22, 30, 35.00, 'UNPAID', NULL),
(2, 23, 40, 20.00, 'PAID', '2026-09-20 14:30:00');

-- 9. VERIFICATION STATS
SELECT 'Students Seeded' AS metric, COUNT(*) AS count FROM `students` UNION ALL
SELECT 'Books Seeded', COUNT(*) FROM `books` UNION ALL
SELECT 'Active Issues', COUNT(*) FROM `issued_books` WHERE status IN ('ISSUED', 'OVERDUE') UNION ALL
SELECT 'Fines Recorded', COUNT(*) FROM `fines`;