CREATE TABLE `users` (
  `id` bigint PRIMARY KEY NOT NULL,
  `social_provider` varchar(255) NOT NULL COMMENT 'KAKAO / GOOGLE / NAVER',
  `social_id` varchar(255) NOT NULL COMMENT 'Unique per provider',
  `email` varchar(255) COMMENT 'nullable',
  `nickname` varchar(255) UNIQUE NOT NULL,
  `profile_image_url` varchar(255),
  `point` int NOT NULL DEFAULT 0,
  `streak_count` int NOT NULL DEFAULT 0,
  `last_completed_date` date,
  `created_at` datetime NOT NULL
);

CREATE TABLE `friendship` (
  `id` bigint PRIMARY KEY NOT NULL,
  `requester_id` bigint NOT NULL,
  `addressee_id` bigint NOT NULL,
  `status` varchar(255) NOT NULL COMMENT 'PENDING / ACCEPTED / BLOCKED',
  `created_at` datetime NOT NULL
);

CREATE TABLE `missions` (
  `id` bigint PRIMARY KEY NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text,
  `category` varchar(255) NOT NULL,
  `difficulty` tinyint NOT NULL COMMENT '1~5',
  `target_object` varchar(255) COMMENT 'AI 인식용 타겟',
  `is_active` tinyint NOT NULL DEFAULT 1
);

CREATE TABLE `bingo_board` (
  `id` bigint PRIMARY KEY NOT NULL,
  `user_id` bigint NOT NULL,
  `mode` varchar(255) NOT NULL COMMENT 'NORMAL / CHALLENGE',
  `category` varchar(255) COMMENT 'CHALLENGE 모드 시 선택 영역',
  `status` varchar(255) NOT NULL COMMENT 'IN_PROGRESS / COMPLETED / EXPIRED',
  `completed_count` int NOT NULL DEFAULT 0,
  `created_at` datetime NOT NULL COMMENT '23:59:59 타임리미트 기준점'
);

CREATE TABLE `bingo_cells` (
  `id` bigint PRIMARY KEY NOT NULL,
  `board_id` bigint NOT NULL,
  `mission_id` bigint NOT NULL,
  `position` tinyint NOT NULL COMMENT '1~9번 칸 위치',
  `status` varchar(255) NOT NULL DEFAULT 'NONE' COMMENT 'NONE / PENDING / SUCCESS / FAIL',
  `proof_image_url` varchar(255),
  `is_completed` tinyint NOT NULL DEFAULT 0,
  `completed_at` datetime
);

CREATE TABLE `point_log` (
  `id` bigint PRIMARY KEY NOT NULL,
  `user_id` bigint NOT NULL,
  `amount` int NOT NULL COMMENT '+ 적립 / - 차감',
  `reason` varchar(255) NOT NULL COMMENT 'DAILY_COMPLETE / STREAK_BONUS 등',
  `created_at` datetime NOT NULL
);

CREATE TABLE `bingo_likes` (
  `id` bigint PRIMARY KEY NOT NULL,
  `board_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `reaction_type` varchar(255) NOT NULL COMMENT '이모지 ID 등',
  `created_at` datetime NOT NULL
);

CREATE UNIQUE INDEX `uq_social` ON `users` (`social_provider`, `social_id`);

ALTER TABLE `friendship` ADD FOREIGN KEY (`requester_id`) REFERENCES `users` (`id`);

ALTER TABLE `friendship` ADD FOREIGN KEY (`addressee_id`) REFERENCES `users` (`id`);

ALTER TABLE `bingo_board` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `bingo_cells` ADD FOREIGN KEY (`board_id`) REFERENCES `bingo_board` (`id`);

ALTER TABLE `bingo_cells` ADD FOREIGN KEY (`mission_id`) REFERENCES `missions` (`id`);

ALTER TABLE `point_log` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `bingo_likes` ADD FOREIGN KEY (`board_id`) REFERENCES `bingo_board` (`id`);

ALTER TABLE `bingo_likes` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);
